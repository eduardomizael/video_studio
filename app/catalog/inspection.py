"""Bounded local inspection; failures never prevent editing metadata."""
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import subprocess
import uuid

from django.conf import settings
from django.utils import timezone


def cache_path(key):
    if not re.fullmatch(r'[a-f0-9]{64}', key):
        raise ValueError('Invalid thumbnail key')
    root = Path(settings.PRIVATE_MEDIA_CACHE).resolve()
    target = (root / f'{key}.jpg').resolve()
    if target.parent != root:
        raise ValueError('Thumbnail outside cache')
    return target


def inspect_video(video, path):
    video.inspected_at = timezone.now()
    video.inspection_message = ''
    video.inspection_status = 'unavailable'
    video.codec = ''
    video.width = video.height = None
    video.size_bytes = None
    video.thumbnail_key = ''
    if video.duration_source != 'manual':
        video.duration_ms = None
        video.duration_source = 'unknown'
    if video.file_status != 'available':
        video.inspection_message = 'O arquivo não está acessível para inspeção. Você pode preencher os dados manualmente.'
        return
    try:
        stat = path.stat()
        video.size_bytes = stat.st_size
        result = subprocess.run([
            settings.FFPROBE_BINARY, '-v', 'error', '-protocol_whitelist', 'file',
            '-format_whitelist', 'mov,matroska,webm,avi,ogg,mpeg,mpegts,flv,asf', '-show_entries',
            'format=duration:stream=codec_type,codec_name,width,height,duration',
            '-of', 'json', str(path),
        ], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=settings.MEDIA_INSPECTION_TIMEOUT, check=True)
        data = json.loads(result.stdout)
        stream = next((item for item in data.get('streams', []) if item.get('codec_type') == 'video'), None)
        if not stream:
            raise ValueError('No video stream')
        raw_duration = data.get('format', {}).get('duration') or stream.get('duration')
        if raw_duration and video.duration_source != 'manual':
            seconds = Decimal(raw_duration)
            if not seconds.is_finite() or seconds < 0:
                raise ValueError('Invalid duration')
            milliseconds = int(seconds * 1000)
            if milliseconds > 9223372036854775807:
                raise ValueError('Invalid duration')
            video.duration_ms = milliseconds
            video.duration_source = 'automatic'
        video.codec = str(stream.get('codec_name', ''))[:80]
        video.width = int(stream['width']) if stream.get('width') else None
        video.height = int(stream['height']) if stream.get('height') else None
        video.inspection_status = 'ready'
    except FileNotFoundError:
        video.inspection_message = 'FFprobe não disponível. Informe a duração e a miniatura manualmente.'
        return
    except (OSError, ValueError, TypeError, InvalidOperation, subprocess.SubprocessError):
        video.inspection_status = 'failed'
        video.inspection_message = 'Não foi possível inspecionar o vídeo. Confira o arquivo ou preencha os dados manualmente.'
        return
    temporary = None
    try:
        key = hashlib.sha256(f'{path}:{stat.st_size}:{stat.st_mtime_ns}'.encode()).hexdigest()
        target = cache_path(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            temporary = target.with_name(f'{uuid.uuid4().hex}.jpg')
            subprocess.run([
                settings.FFMPEG_BINARY, '-nostdin', '-v', 'error', '-protocol_whitelist', 'file',
                '-format_whitelist', 'mov,matroska,webm,avi,ogg,mpeg,mpegts,flv,asf', '-i', str(path),
                '-frames:v', '1', '-vf', 'scale=640:-2', '-q:v', '3', '-y', str(temporary),
            ], capture_output=True, timeout=settings.MEDIA_INSPECTION_TIMEOUT, check=True)
            if not temporary.is_file() or not temporary.stat().st_size:
                raise ValueError('No thumbnail')
            temporary.replace(target)
        video.thumbnail_key = key
    except (OSError, ValueError, subprocess.SubprocessError):
        video.inspection_message = 'Dados técnicos extraídos; miniatura indisponível. Selecione uma imagem local manualmente.'
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
