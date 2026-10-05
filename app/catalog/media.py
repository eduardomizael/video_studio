"""Authenticated local delivery with bounded single-range streaming."""
import mimetypes
import os
import re

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import FileResponse, Http404, HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils.http import http_date, parse_http_date_safe
from django.views.decorators.http import require_http_methods

from .inspection import cache_path
from .models import Video
from .paths import resolve_media_path


def available_path(video):
    try:
        path, _, _ = resolve_media_path(video.local_midia, video.relative_path)
        return path
    except ValidationError as exc:
        raise Http404('Referência de mídia indisponível.') from exc


def range_bytes(stream, start, length):
    try:
        stream.seek(start)
        while length:
            chunk = stream.read(min(64 * 1024, length))
            if not chunk:
                break
            length -= len(chunk)
            yield chunk
    finally:
        stream.close()


def parse_range(value, size):
    match = re.fullmatch(r'bytes=(\d{0,19})-(\d{0,19})', value)
    if not match or not size:
        raise ValueError('Invalid range')
    first, last = match.groups()
    if not first:
        if not last or int(last) == 0:
            raise ValueError('Invalid suffix')
        return max(0, size - int(last)), size - 1
    start = int(first)
    end = min(int(last), size - 1) if last else size - 1
    if start >= size or end < start:
        raise ValueError('Unsatisfiable range')
    return start, end


def protected_headers(response):
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    response['Vary'] = 'Cookie'
    return response


@login_required
@require_http_methods(['GET', 'HEAD'])
def media_file(request, video_id):
    if settings.UI_DEMO:
        return HttpResponse(status=403)
    video = get_object_or_404(Video.objects.select_related('local_midia'), pk=video_id)
    path = available_path(video)
    mime = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
    if mime == 'application/ogg':
        mime = 'video/ogg'
    # Cataloging arbitrary references must never expose HTML or other active content inline.
    if not mime.startswith('video/'):
        return protected_headers(HttpResponse('Formato não disponível no player.', status=415))
    try:
        stream = path.open('rb')
        stat = os.fstat(stream.fileno())
    except OSError as exc:
        raise Http404('Arquivo não encontrado ou sem acesso.') from exc
    size = stat.st_size
    etag = f'"{size:x}-{stat.st_mtime_ns:x}"'
    range_value = request.headers.get('Range')
    if_range = request.headers.get('If-Range')
    if if_range and range_value:
        date = parse_http_date_safe(if_range)
        if if_range != etag and (date is None or date < int(stat.st_mtime)):
            range_value = None
    start, end = 0, size - 1
    if range_value:
        try:
            start, end = parse_range(range_value, size)
        except ValueError:
            stream.close()
            response = HttpResponse(status=416)
            response['Content-Range'] = f'bytes */{size}'
            response['Accept-Ranges'] = 'bytes'
            return protected_headers(response)
    if request.method == 'HEAD':
        stream.close()
        response = HttpResponse(content_type=mime, status=206 if range_value else 200)
    elif range_value:
        response = StreamingHttpResponse(range_bytes(stream, start, end - start + 1), content_type=mime, status=206)
        # Close even if the iterator is never consumed (client disconnect/server cleanup).
        response._resource_closers.append(stream.close)
    else:
        response = FileResponse(stream, content_type=mime)
    response['Content-Length'] = str(end - start + 1)
    response['Accept-Ranges'] = 'bytes'
    response['ETag'] = etag
    response['Last-Modified'] = http_date(stat.st_mtime)
    if range_value:
        response['Content-Range'] = f'bytes {start}-{end}/{size}'
    return protected_headers(response)


@login_required
@require_http_methods(['GET', 'HEAD'])
def thumbnail(request, video_id):
    if settings.UI_DEMO:
        return HttpResponse(status=403)
    video = get_object_or_404(Video.objects.select_related('local_midia'), pk=video_id)
    if not video.local_midia.active:
        raise Http404('Local de mídia desativado.')
    try:
        # Resolve the video reference again to prevent cache access after root/path tampering.
        available_path(video)
        if video.thumbnail_relative_path:
            path, _, _ = resolve_media_path(video.local_midia, video.thumbnail_relative_path)
            if path.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp', '.gif'}:
                raise ValueError('Unsupported image')
            mime = mimetypes.guess_type(path.name)[0]
        elif video.thumbnail_key:
            path = cache_path(video.thumbnail_key)
            mime = 'image/jpeg'
        else:
            raise Http404('Miniatura ainda não disponível.')
        stream = path.open('rb')
    except (OSError, ValidationError, ValueError) as exc:
        raise Http404('Miniatura indisponível.') from exc
    if request.method == 'HEAD':
        response = HttpResponse(content_type=mime)
        response['Content-Length'] = str(os.fstat(stream.fileno()).st_size)
        stream.close()
    else:
        response = FileResponse(stream, content_type=mime)
    return protected_headers(response)
