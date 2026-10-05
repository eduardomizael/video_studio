from pathlib import PurePosixPath
from django.urls import reverse
from django.utils import timezone


def video_data(video):
    duration = 'Duração desconhecida'
    if video.duration_ms is not None:
        seconds = video.duration_ms // 1000
        duration = f'{seconds // 3600:02}:{seconds // 60 % 60:02}:{seconds % 60:02}'
    return {
        'id': video.pk, 'title': video.title, 'description': video.description,
        'filename': PurePosixPath(video.relative_path).name,
        'duration': duration, 'duration_seconds': (video.duration_ms or 0) / 1000,
        'tags': [tag.name for tag in video.tags.all()],
        'people': [person.name for person in video.people.all()],
        'status': video.get_file_status_display(),
        'tone': 'green' if video.file_status == 'available' else 'muted',
        'thumb': 'unavailable', 'codec': video.codec or 'Não identificado',
        'resolution': f'{video.width} × {video.height}' if video.width and video.height else '—',
        'size': f'{video.size_bytes / 1024 / 1024:.1f} MB' if video.size_bytes is not None else '—',
        'thumbnail_url': reverse('studio:thumbnail', args=[video.pk]) if video.thumbnail_key or video.thumbnail_relative_path else '',
        'updated': timezone.localtime(video.updated_at).strftime('%d/%m/%Y %H:%M'),
        'editor_url': reverse('studio:editor', args=[video.pk]),
        'chapters_url': reverse('studio:chapters', args=[video.pk]),
    }
