from django.urls import path
from . import views
from app.catalog import views as catalog_views
from app.catalog import media

app_name = 'studio'
urlpatterns = [
    path('', views.library, name='library'),
    path('videos/novo/', catalog_views.create_video, name='create_video'),
    path('videos/<int:video_id>/salvar/', catalog_views.update_video, name='update_video'),
    path('videos/<int:video_id>/midia/', media.media_file, name='media_file'),
    path('videos/<int:video_id>/miniatura/', media.thumbnail, name='thumbnail'),
    path('videos/<int:video_id>/inspecionar/', catalog_views.reinspect, name='reinspect'),
    path('videos/<int:video_id>/', views.editor, name='editor'),
    path('videos/<int:video_id>/capitulos/', views.chapters, name='chapters'),
    path('perfil/', views.profile, name='profile'),
    path('componentes/', views.components, name='components'),
]
