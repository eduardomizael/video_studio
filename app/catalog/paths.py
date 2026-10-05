import os
from pathlib import Path, PureWindowsPath

from django.core.exceptions import ValidationError


def resolve_media_path(local, relative_path):
    """Validate containment even when the referenced file does not exist."""
    if not local or not local.active:
        raise ValidationError('Selecione um local de mídia ativo.')
    raw = relative_path.strip().replace('\\', '/')
    windows = PureWindowsPath(raw)
    if not raw or '\x00' in raw or Path(raw).is_absolute() or windows.drive or windows.root:
        raise ValidationError('Informe somente um caminho relativo ao local de mídia.')
    if '..' in raw.split('/'):
        raise ValidationError('O caminho não pode conter segmentos "..".')
    if ':' in raw:
        raise ValidationError('O caminho não pode conter dois-pontos ou referências a fluxos alternativos.')
    if not Path(local.root_path).is_absolute():
        raise ValidationError('A raiz do local de mídia precisa ser absoluta no servidor.')
    try:
        root = Path(local.root_path).resolve()
        target = (root / raw).resolve()
        relative = target.relative_to(root)
        if not relative.parts or (target.exists() and not target.is_file()):
            raise ValidationError('A referência deve apontar para um arquivo, não uma pasta.')
    except (ValueError, OSError, RuntimeError) as exc:
        raise ValidationError('O caminho não pertence ao local autorizado ou não pode ser resolvido.') from exc
    normalized = relative.as_posix()
    return target, normalized, os.path.normcase(normalized)
