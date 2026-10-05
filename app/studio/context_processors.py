from django.conf import settings
from .demo import NOTIFICATIONS

def studio_shell(request):
    if not settings.UI_DEMO:
        user = request.user
        name = (user.get_full_name() or user.email) if user.is_authenticated else 'Visitante'
        from app.catalog.forms import VideoForm
        return {
            'ui_demo': False,
            'studio_user': {'name': name, 'email': user.email if user.is_authenticated else '', 'initials': ''.join(part[0] for part in name.split()[:2]).upper()},
            'notifications': [],
            'new_video_form': VideoForm(auto_id='new_%s') if user.is_authenticated else None,
        }
    return {
        'ui_demo': settings.UI_DEMO,
        'studio_user': {'name': 'Lucas Mendes', 'email': 'lucas@example.com', 'initials': 'LM'},
        'notifications': NOTIFICATIONS,
    }
