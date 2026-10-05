from django.db import transaction
from django.utils import timezone

from app.catalog.models import Video
from .models import SubtitleEntry, SubtitleVersion


def stamp(video_id, actor, version=None):
    now = timezone.now()
    Video.objects.filter(pk=video_id).update(updated_by=actor, updated_at=now)
    if version:
        SubtitleVersion.objects.filter(pk=version.pk).update(updated_by=actor, updated_at=now)


@transaction.atomic
def import_version(form, actor):
    version = form.save(commit=False)
    version.video = Video.objects.select_for_update().get(pk=version.video_id)
    version.active = not version.video.subtitle_versions.filter(active=True).exists()
    version.created_by = version.updated_by = actor
    version.full_clean()
    version.save()
    entries = [SubtitleEntry(version=version, **data) for data in form.entries]
    for entry in entries:
        entry.full_clean()
    SubtitleEntry.objects.bulk_create(entries)
    stamp(version.video_id, actor)
    return version


@transaction.atomic
def activate_version(version, actor):
    Video.objects.select_for_update().get(pk=version.video_id)
    version.video.subtitle_versions.filter(active=True).update(active=False)
    SubtitleVersion.objects.filter(pk=version.pk).update(active=True)
    stamp(version.video_id, actor, version)


@transaction.atomic
def save_version(form, actor):
    version = form.save(commit=False)
    Video.objects.select_for_update().get(pk=version.video_id)
    version.active = SubtitleVersion.objects.get(pk=version.pk).active
    version.full_clean()
    version.updated_by = actor
    version.save(update_fields=['name', 'language', 'updated_by', 'updated_at'])
    stamp(version.video_id, actor)
    return version


@transaction.atomic
def save_entry(form, actor):
    entry = form.save(commit=False)
    video = Video.objects.select_for_update().get(pk=entry.version.video_id)
    entry.version.video = video
    entry.full_clean()
    if not entry.pk:
        from django.core.exceptions import ValidationError
        if entry.version.entries.count() >= 5000:
            raise ValidationError('A versão já possui 5.000 entradas.')
        entry.order = (entry.version.entries.order_by('-order').values_list('order', flat=True).first() or 0) + 1
    entry.save()
    stamp(video.pk, actor, entry.version)
    return entry


@transaction.atomic
def delete_entry(entry, actor):
    video_id, version = entry.version.video_id, entry.version
    Video.objects.select_for_update().get(pk=video_id)
    entry.delete()
    stamp(video_id, actor, version)
