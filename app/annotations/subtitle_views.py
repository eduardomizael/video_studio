from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .subtitle_forms import EntryForm, ImportForm, VersionForm
from .subtitle_services import activate_version, delete_entry, import_version, save_entry, save_version
from .timecodes import format_timecode
from .views import get_video


def version_for(video, version_id):
    return get_object_or_404(video.subtitle_versions.all(), pk=version_id)


def respond(request, video, version=None, form=None, editing=None, status=200):
    versions = list(video.subtitle_versions.all())
    if version is None and versions:
        version = next((item for item in versions if item.active), versions[0])
    page = Paginator(version.entries.all(), 50).get_page(request.GET.get('page')) if version else None
    if page:
        for entry in page:
            entry.start_label = format_timecode(entry.start_ms)
            entry.end_label = format_timecode(entry.end_ms)
    return render(request, 'studio/real_subtitles.html', {
        'page': 'chapters', 'page_title': 'Legendas SRT', 'record': video,
        'versions': versions, 'selected_version': version, 'entries_page': page,
        'import_form': form if isinstance(form, ImportForm) else ImportForm(video=video),
        'version_form': form if isinstance(form, VersionForm) and not isinstance(form, ImportForm) else VersionForm(instance=version) if version else None,
        'entry_form': form if isinstance(form, EntryForm) else EntryForm(version=version) if version else None,
        'editing_entry': editing,
    }, status=status)


def error_on(form, error):
    if isinstance(error, ValidationError) and hasattr(error, 'message_dict'):
        for key, errors in error.message_dict.items():
            form.add_error(key if key in form.fields else None, errors)
    else:
        form.add_error(None, error if isinstance(error, ValidationError) else 'Conflito de dados. Recarregue e tente novamente.')


@login_required
@require_GET
def index(request, video_id, version_id=None):
    if settings.UI_DEMO:
        return HttpResponseForbidden('Desative a prévia para acessar legendas reais.')
    video = get_video(video_id)
    return respond(request, video, version_for(video, version_id) if version_id else None)


@login_required
@require_POST
def import_srt(request, video_id):
    if settings.UI_DEMO:
        return HttpResponseForbidden('A prévia não importa legendas reais.')
    video = get_video(video_id)
    form = ImportForm(request.POST, request.FILES, video=video)
    if form.is_valid():
        try:
            version = import_version(form, request.user)
        except (ValidationError, IntegrityError) as error:
            error_on(form, error)
        else:
            messages.success(request, 'Versão SRT importada. Todas as entradas foram gravadas.')
            return redirect('studio:subtitle_version', video_id=video.pk, version_id=version.pk)
    return respond(request, video, form=form, status=400)


@login_required
@require_POST
def version_action(request, video_id, version_id, action):
    if settings.UI_DEMO:
        return HttpResponseForbidden('A prévia não altera legendas reais.')
    video = get_video(video_id)
    version = version_for(video, version_id)
    if action == 'activate':
        activate_version(version, request.user)
        messages.success(request, 'Versão ativa atualizada. Reabra o player para carregar esta versão.')
    else:
        form = VersionForm(request.POST, instance=version)
        if form.is_valid():
            try:
                save_version(form, request.user)
            except (ValidationError, IntegrityError) as error:
                error_on(form, error)
            else:
                return redirect('studio:subtitle_version', video_id=video.pk, version_id=version.pk)
        return respond(request, video, version, form, status=400)
    return redirect('studio:subtitle_version', video_id=video.pk, version_id=version.pk)


@login_required
@require_GET
def edit_entry(request, video_id, version_id, entry_id):
    if settings.UI_DEMO:
        return HttpResponseForbidden('A prévia não edita legendas reais.')
    video = get_video(video_id)
    version = version_for(video, version_id)
    entry = get_object_or_404(version.entries.all(), pk=entry_id)
    return respond(request, video, version, EntryForm(instance=entry, version=version), entry)


@login_required
@require_POST
def entry_save(request, video_id, version_id, entry_id=None):
    if settings.UI_DEMO:
        return HttpResponseForbidden('A prévia não grava legendas reais.')
    video = get_video(video_id)
    version = version_for(video, version_id)
    entry = get_object_or_404(version.entries.all(), pk=entry_id) if entry_id else None
    form = EntryForm(request.POST, instance=entry, version=version)
    if form.is_valid():
        try:
            save_entry(form, request.user)
        except (ValidationError, IntegrityError) as error:
            error_on(form, error)
        else:
            messages.success(request, 'Entrada de legenda salva.')
            return redirect('studio:subtitle_version', video_id=video.pk, version_id=version.pk)
    return respond(request, video, version, form, entry, status=400)


@login_required
@require_GET
def confirm_remove(request, video_id, version_id, entry_id):
    if settings.UI_DEMO:
        return HttpResponseForbidden('A prévia não remove legendas reais.')
    video = get_video(video_id)
    version = version_for(video, version_id)
    entry = get_object_or_404(version.entries.all(), pk=entry_id)
    return render(request, 'studio/confirm_subtitle_delete.html', {'page': 'chapters', 'record': video, 'version': version, 'entry': entry})


@login_required
@require_POST
def remove_entry(request, video_id, version_id, entry_id):
    if settings.UI_DEMO:
        return HttpResponseForbidden('A prévia não remove legendas reais.')
    video = get_video(video_id)
    version = version_for(video, version_id)
    entry = get_object_or_404(version.entries.all(), pk=entry_id)
    delete_entry(entry, request.user)
    messages.success(request, 'Entrada removida. A versão e o vídeo foram preservados.')
    return redirect('studio:subtitle_version', video_id=video.pk, version_id=version.pk)
