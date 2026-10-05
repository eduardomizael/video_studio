from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import F, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import VideoForm
from .models import LocalMidia, Pessoa, Tag, Video
from .presentation import video_data
from .services import save_video, file_status
from .paths import resolve_media_path
from .inspection import inspect_video


def video_queryset():
    return Video.objects.select_related('local_midia', 'created_by', 'updated_by').prefetch_related('tags', 'people')


def selected_ids(request, key):
    # Invalid submitted IDs must not silently remove the filter and expose a larger result set.
    return [value if value.isdecimal() and len(value) < 19 else '0' for value in request.GET.getlist(key) if value]


@login_required
def library(request):
    query = request.GET.get('q', '').strip()
    tags = selected_ids(request, 'tag')
    people = selected_ids(request, 'person')
    sort = request.GET.get('sort', 'recent')
    queryset = video_queryset()
    if query:
        queryset = queryset.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if tags:
        queryset = queryset.filter(tags__pk__in=tags)
    if people:
        queryset = queryset.filter(people__pk__in=people)
    ordering = {
        'recent': ['-updated_at', '-pk'],
        'title': ['title', 'pk'],
        'duration': [F('duration_ms').desc(nulls_last=True), 'pk'],
    }
    if sort not in ordering:
        sort = 'recent'
    queryset = queryset.distinct().order_by(*ordering[sort])
    paginator = Paginator(queryset, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    videos = [video_data(video) for video in page_obj.object_list]
    params = request.GET.copy()
    params.pop('page', None)
    is_htmx = request.headers.get('HX-Request') == 'true'
    context = {
        'page': 'library', 'page_title': 'Biblioteca de Mídia', 'is_htmx': is_htmx,
        'videos': videos, 'all_videos': videos, 'selected_video': videos[0] if videos else None,
        'query': query, 'selected_tags': tags, 'selected_people': people, 'sort': sort,
        'tags': Tag.objects.all(), 'people': Pessoa.objects.all(),
        'total': Video.objects.count(), 'filtered_total': paginator.count, 'page_obj': page_obj,
        'page_query': params.urlencode(), 'has_media_locations': LocalMidia.objects.filter(active=True).exists(),
    }
    template = 'studio/partials/real_library_results.html' if is_htmx else 'studio/real_library.html'
    return render(request, template, context)


@login_required
def editor(request, video_id):
    video = get_object_or_404(video_queryset(), pk=video_id)
    return render_editor(request, VideoForm(instance=video), video)


def render_editor(request, form, video=None, status=200):
    media_available = False
    if video:
        try:
            path, _, _ = resolve_media_path(video.local_midia, video.relative_path)
            video.file_status = file_status(path)
            media_available = video.file_status == Video.FileStatus.AVAILABLE
        except ValidationError:
            video.file_status = Video.FileStatus.UNREADABLE
    return render(request, 'studio/real_editor.html', {
        'page': 'editor', 'page_title': 'Editar vídeo' if video else 'Cadastrar vídeo',
        'form': form, 'record': video, 'video': video_data(video) if video else None, 'media_available': media_available,
    }, status=status)


def form_save_error(form, error):
    if isinstance(error, ValidationError):
        if hasattr(error, 'message_dict'):
            for field, errors in error.message_dict.items():
                form.add_error(field if field in form.fields else None, errors)
        else:
            form.add_error(None, error)
    else:
        form.add_error(None, 'Não foi possível salvar por um conflito de dados. Recarregue e confira a referência de mídia.')


@login_required
@require_POST
def create_video(request):
    if settings.UI_DEMO:
        return HttpResponseForbidden('A prévia não grava dados. Desative UI_DEMO para usar o catálogo.')
    form = VideoForm(request.POST)
    if form.is_valid():
        try:
            video = save_video(form, request.user)
        except (ValidationError, IntegrityError) as error:
            form_save_error(form, error)
        else:
            messages.success(request, 'Vídeo cadastrado. Os dados foram gravados no catálogo.')
            return redirect('studio:editor', video_id=video.pk)
    return render_editor(request, form, status=400)


@login_required
@require_POST
def update_video(request, video_id):
    if settings.UI_DEMO:
        return HttpResponseForbidden('A prévia não grava dados. Desative UI_DEMO para usar o catálogo.')
    video = get_object_or_404(video_queryset(), pk=video_id)
    form = VideoForm(request.POST, instance=video)
    if form.is_valid():
        try:
            saved = save_video(form, request.user)
        except (ValidationError, IntegrityError) as error:
            form_save_error(form, error)
        else:
            messages.success(request, 'Metadados e associações salvos.')
            return redirect('studio:editor', video_id=saved.pk)
    # ModelForm mutates its instance while validating; use persisted data for the summary.
    video.refresh_from_db()
    return render_editor(request, form, video, status=400)


@login_required
@require_POST
def reinspect(request, video_id):
    if settings.UI_DEMO:
        return HttpResponseForbidden('A prévia não inspeciona arquivos reais.')
    video = get_object_or_404(video_queryset(), pk=video_id)
    try:
        path, _, _ = resolve_media_path(video.local_midia, video.relative_path)
        video.file_status = file_status(path)
        inspect_video(video, path)
        video.updated_by = request.user
        video.save()
    except ValidationError:
        messages.error(request, 'A referência não está disponível em um local ativo. Confira o caminho e o local.')
    else:
        messages.info(request, video.inspection_message or 'Inspeção técnica concluída.')
    return redirect('studio:editor', video_id=video.pk)
