from django import template

register = template.Library()


@register.simple_tag
def active_subtitle_data(video):
    version = video.subtitle_versions.filter(active=True).first()
    if not version:
        return {'name': '', 'entries': []}
    return {'name': version.name, 'entries': list(version.entries.values('start_ms', 'end_ms', 'text'))}
