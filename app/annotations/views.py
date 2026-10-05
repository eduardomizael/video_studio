from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from app.catalog.models import Video
from app.catalog.presentation import video_data
from app.catalog.services import file_status
from app.catalog.paths import resolve_media_path
from .forms import MarkingForm
from .models import MarcacaoTemporal
from .services import delete_marking, save_marking
from .timecodes import format_timecode


def get_video(video_id):
    return get_object_or_404(Video.objects.select_related('local_midia', 'updated_by').prefetch_related('tags', 'people'), pk=video_id)


def markings_for(video):
    return video.markings.select_related('created_by', 'updated_by').prefetch_related('tags', 'people')


def render_chapters(request, video, form=None, editing=None, status=200):
    available = False
    try:
        path, _, _ = resolve_media_path(video.local_midia, video.relative_path)
        video.file_status = file_status(path)
        available = video.file_status == Video.FileStatus.AVAILABLE
    except ValidationError:
        video.file_status = Video.FileStatus.UNREADABLE
    markings = list(markings_for(video))
    for marking in markings:
        marking.start_label = format_timecode(marking.start_ms)
        marking.end_label = format_timecode(marking.end_ms) if marking.end_ms is not None else ''
    return render(request, 'studio/real_chapters.html', {
        'page': 'chapters', 'page_title': 'Capítulos e marcações', 'record': video, 'video': video_data(video),
        'media_available': available, 'markings': markings, 'form': form if form is not None else MarkingForm(video=video), 'editing': editing,
    }, status=status)


@login_required
@require_GET
def chapters(request, video_id):
    return render_chapters(request, get_video(video_id))


@login_required
@require_POST
def create(request, video_id):
    if settings.UI_DEMO:
        return HttpResponseForbidden('A prévia não grava marcações reais.')
    video = get_video(video_id)
    return save_response(request, video, MarkingForm(request.POST, video=video))


@login_required
@require_GET
def edit(request, video_id, marking_id):
    if settings.UI_DEMO:
        return HttpResponseForbidden('A prévia não edita marcações reais.')
    video = get_video(video_id)
    marking = get_object_or_404(markings_for(video), pk=marking_id)
    return render_chapters(request, video, MarkingForm(instance=marking, video=video), marking)


@login_required
@require_POST
def update(request, video_id, marking_id):
    if settings.UI_DEMO:
        return HttpResponseForbidden('A prévia não grava marcações reais.')
    video = get_video(video_id)
    marking = get_object_or_404(markings_for(video), pk=marking_id)
    return save_response(request, video, MarkingForm(request.POST, instance=marking, video=video), marking)


def save_response(request, video, form, editing=None):
    if form.is_valid():
        try:
            save_marking(form, request.user)
        except ValidationError as error:
            if hasattr(error, 'message_dict'):
                for key, errors in error.message_dict.items():
                    form.add_error(key if key in form.fields else None, errors)
            else:
                form.add_error(None, error)
        except IntegrityError:
            form.add_error(None, 'O registro mudou durante o salvamento. Confira os dados e tente novamente.')
        else:
            messages.success(request, 'Marcação salva no catálogo.')
            return redirect('studio:chapters', video_id=video.pk)
    return render_chapters(request, video, form, editing, status=400)


@login_required
@require_GET
def confirm_delete(request, video_id, marking_id):
    if settings.UI_DEMO:
        return HttpResponseForbidden('A prévia não remove marcações reais.')
    video = get_video(video_id)
    marking = get_object_or_404(markings_for(video), pk=marking_id)
    return render(request, 'studio/confirm_marking_delete.html', {'page': 'chapters', 'page_title': 'Remover marcação', 'record': video, 'marking': marking})


@login_required
@require_POST
def remove(request, video_id, marking_id):
    if settings.UI_DEMO:
        return HttpResponseForbidden('A prévia não remove marcações reais.')
    video = get_video(video_id)
    marking = get_object_or_404(markings_for(video), pk=marking_id)
    delete_marking(marking, request.user)
    messages.success(request, 'Marcação removida. O vídeo e os cadastros de tags/pessoas foram preservados.')
    return redirect('studio:chapters', video_id=video.pk)
