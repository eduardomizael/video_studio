import unicodedata

from django.db import transaction

from .models import Pessoa, Tag, Video, normalize_tag
from .paths import resolve_media_path
from .inspection import inspect_video


def file_status(path):
    try:
        if not path.exists():
            return Video.FileStatus.MISSING
        with path.open('rb') as stream:
            stream.read(1)
        return Video.FileStatus.AVAILABLE
    except FileNotFoundError:
        return Video.FileStatus.MISSING
    except OSError:
        return Video.FileStatus.UNREADABLE


def save_video(form, actor):
    video = form.save(commit=False)
    previous = Video.objects.filter(pk=video.pk).first() if video.pk else None
    reference_changed = not previous or previous.local_midia_id != video.local_midia_id or previous.relative_path != video.relative_path
    manual_changed = video.duration_ms is not None and (not previous or previous.duration_ms != video.duration_ms)
    if manual_changed:
        video.duration_source = 'manual'
    elif video.duration_ms is None or reference_changed:
        video.duration_ms = None
        video.duration_source = 'unknown'
    path, video.relative_path, video.path_key = resolve_media_path(video.local_midia, video.relative_path)
    video.full_clean()
    video.file_status = file_status(path)
    if reference_changed or video.duration_source == 'unknown' or previous and previous.file_status != video.file_status:
        inspect_video(video, path)
    if not video.pk:
        video.created_by = actor
    video.updated_by = actor
    with transaction.atomic():
        video.save()
        form.save_m2m()
        for name in form.cleaned_data['new_tags']:
            display = ' '.join(unicodedata.normalize('NFKC', name).split())
            tag, _ = Tag.objects.get_or_create(normalized_name=normalize_tag(display), defaults={'name': display})
            video.tags.add(tag)
        name = form.cleaned_data['new_person_name']
        if name:
            person = Pessoa.objects.create(name=name, notes=form.cleaned_data['new_person_notes'])
            video.people.add(person)
    return video
