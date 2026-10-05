import re

from django.core.exceptions import ValidationError


def format_timecode(milliseconds):
    seconds, fraction = divmod(milliseconds, 1000)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f'{hours:02}:{minutes:02}:{seconds:02}.{fraction:03}'


def parse_timecode(value):
    match = re.fullmatch(r'(\d+):(\d{2})(?::(\d{2}))?(?:[.,](\d{1,3}))?', value.strip())
    if not match:
        raise ValidationError('Use MM:SS.mmm ou HH:MM:SS.mmm, sem valores negativos.')
    first, second, third, fraction = match.groups()
    if len(first) > 15 or int(second) >= 60 or third is not None and int(third) >= 60:
        raise ValidationError('Informe um tempo válido; minutos/segundos após os dois-pontos devem ser menores que 60.')
    seconds = int(first) * 60 + int(second) if third is None else int(first) * 3600 + int(second) * 60 + int(third)
    result = seconds * 1000 + int((fraction or '').ljust(3, '0') or 0)
    if result > 9223372036854775807:
        raise ValidationError('O tempo excede a capacidade de armazenamento.')
    return result
