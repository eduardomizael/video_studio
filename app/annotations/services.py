from django.db import transaction
from django.utils import timezone

from app.catalog.models import Video


@transaction.atomic
def save_marking(form, actor):
    marking = form.save(commit=False)
    marking.video = Video.objects.select_for_update().get(pk=marking.video_id)
    marking.full_clean()
    if not marking.pk:
        marking.created_by = actor
    marking.updated_by = actor
    marking.save()
    form.save_m2m()
    Video.objects.filter(pk=marking.video_id).update(updated_by=actor, updated_at=timezone.now())
    return marking


@transaction.atomic
def delete_marking(marking, actor):
    Video.objects.select_for_update().get(pk=marking.video_id)
    marking.delete()
    Video.objects.filter(pk=marking.video_id).update(updated_by=actor, updated_at=timezone.now())
