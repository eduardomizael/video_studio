from functools import wraps
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET
from .demo import VIDEOS, CHAPTERS, SUBTITLES
from app.catalog import views as catalog_views
from app.catalog.models import Video
from django.shortcuts import get_object_or_404

def preview_access(view):
    """Public local preview; require a real session when UI_DEMO is disabled."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if settings.UI_DEMO:
            return view(request, *args, **kwargs)
        return login_required(view)(request, *args, **kwargs)
    return wrapper

def video_context(video_id):
    video = next((item for item in VIDEOS if item['id'] == video_id), None)
    if video is None:
        raise Http404('Vídeo não encontrado.')
    duration = video['duration_seconds']
    chapters = []
    for item in CHAPTERS:
        if item['seconds'] < duration:
            minutes, seconds = map(int, item['length'].split(':'))
            chapters.append({**item, 'end_seconds': min(duration, item['seconds'] + minutes * 60 + seconds)})
    def subtitle_end(item):
        hours, minutes, seconds = map(float, item['end'].split(':'))
        return hours * 3600 + minutes * 60 + seconds
    subtitles = [item for item in SUBTITLES if subtitle_end(item) <= duration]
    return {'video': video, 'chapters': chapters, 'subtitles': subtitles}

@preview_access
@require_GET
def library(request):
    if not settings.UI_DEMO:
        return catalog_views.library(request)
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    tag = request.GET.get('tag', '')
    person = request.GET.get('person', '')
    sort = request.GET.get('sort', 'recent')
    videos = [v for v in VIDEOS if
        (not query or query.casefold() in (v['title'] + ' ' + v['description'] + ' ' + ' '.join(v['tags'])).casefold()) and
        (not category or v['category'] == category) and
        (not tag or tag in v['tags']) and (not person or person in v['people'])]
    if sort == 'title':
        videos = sorted(videos, key=lambda v: v['title'])
    elif sort == 'duration':
        videos = sorted(videos, key=lambda v: v['duration_seconds'], reverse=True)
    context = {
        'page': 'library', 'page_title': 'Biblioteca de Mídia', 'videos': videos,
        'all_videos': [{**v, 'editor_url': reverse('studio:editor', args=[v['id']]), 'chapters_url': reverse('studio:chapters', args=[v['id']])} for v in VIDEOS],
        'selected_video': VIDEOS[0], 'query': query, 'category': category,
        'tag': tag, 'person': person, 'sort': sort, 'total': len(VIDEOS),
        'categories': ['Vídeos Master', 'Cortes & Shorts', 'Faixas de Áudio & Pods', 'Miniaturas & Imagens', 'B-roll'],
        'tags': sorted({t for v in VIDEOS for t in v['tags']}),
        'people': ['Lucas Mendes', 'Beatriz Santos'],
    }
    template = 'studio/partials/library_results.html' if request.headers.get('HX-Request') == 'true' else 'studio/library.html'
    return render(request, template, context)

@preview_access
@require_GET
def editor(request, video_id=1):
    if not settings.UI_DEMO:
        return catalog_views.editor(request, video_id)
    return render(request, 'studio/editor.html', {'page': 'editor', 'page_title': 'Editor de Vídeo & Metadados', **video_context(video_id)})

@preview_access
@require_GET
def chapters(request, video_id=1):
    if not settings.UI_DEMO:
        video = get_object_or_404(Video, pk=video_id)
        return render(request, 'studio/pending.html', {'page': 'chapters', 'page_title': 'Capítulos e legendas', 'record': video})
    return render(request, 'studio/chapters.html', {'page': 'chapters', 'page_title': 'Capítulos e Legendas', **video_context(video_id)})

@preview_access
@require_GET
def profile(request):
    if not settings.UI_DEMO:
        return render(request, 'studio/real_profile.html', {'page': 'profile', 'page_title': 'Minha conta'})
    return render(request, 'studio/profile.html', {'page': 'profile', 'page_title': 'Perfil & Configurações do Studio'})

@preview_access
@require_GET
def components(request):
    if not settings.UI_DEMO:
        return render(request, 'studio/pending.html', {'page': 'components', 'page_title': 'Notificações'})
    return render(request, 'studio/components.html', {'page': 'components', 'page_title': 'Menus & Notificações', **video_context(1)})
