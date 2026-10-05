import re

from django.core.exceptions import ValidationError

MAX_BYTES = 2 * 1024 * 1024
MAX_ENTRIES = 5000
TIMING = re.compile(r'^(\d{2,12}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2,12}):(\d{2}):(\d{2})[,.](\d{3})$')


def parse_srt(content, duration_ms=None):
    if len(content) > MAX_BYTES:
        raise ValidationError('O SRT deve ter no máximo 2 MB.')
    try:
        text = content.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise ValidationError('Salve o SRT com codificação UTF-8 e tente novamente.') from exc
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    result, index = [], 0
    while index < len(lines):
        if not lines[index].strip():
            index += 1
            continue
        if lines[index].strip().isdigit():
            index += 1
        line_number = index + 1
        match = TIMING.fullmatch(lines[index].strip()) if index < len(lines) else None
        if not match:
            raise ValidationError(f'Linha {line_number}: esperado intervalo HH:MM:SS,mmm --> HH:MM:SS,mmm.')
        values = list(map(int, match.groups()))
        if any(values[n] >= 60 for n in [1, 2, 5, 6]) or any(values[n] > 2500000000 for n in [0, 4]):
            raise ValidationError(f'Linha {line_number}: tempo inválido.')
        start = ((values[0] * 60 + values[1]) * 60 + values[2]) * 1000 + values[3]
        end = ((values[4] * 60 + values[5]) * 60 + values[6]) * 1000 + values[7]
        if end <= start or duration_ms is not None and end > duration_ms:
            raise ValidationError(f'Linha {line_number}: intervalo invertido, vazio ou além da duração do vídeo.')
        index += 1
        body = []
        while index < len(lines) and lines[index].strip():
            body.append(lines[index])
            index += 1
        caption = '\n'.join(body).strip()
        if not caption or len(caption) > 10000 or '\x00' in caption:
            raise ValidationError(f'Linha {line_number}: texto vazio, inválido ou maior que 10.000 caracteres.')
        result.append({'start_ms': start, 'end_ms': end, 'text': caption, 'order': len(result) + 1})
        if len(result) > MAX_ENTRIES:
            raise ValidationError('O SRT deve ter no máximo 5.000 entradas.')
    if not result:
        raise ValidationError('O SRT não contém entradas de legenda.')
    return result
