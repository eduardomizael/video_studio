from django.urls import path
from . import views
from app.catalog import views as catalog_views
from app.catalog import media
from app.annotations import views as annotations
from app.annotations import subtitle_views as subtitles

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
    path('videos/<int:video_id>/legendas/', subtitles.index, name='subtitles'),
    path('videos/<int:video_id>/legendas/importar/', subtitles.import_srt, name='import_srt'),
    path('videos/<int:video_id>/legendas/<int:version_id>/', subtitles.index, name='subtitle_version'),
    path('videos/<int:video_id>/legendas/<int:version_id>/ativar/', subtitles.version_action, {'action': 'activate'}, name='activate_subtitles'),
    path('videos/<int:video_id>/legendas/<int:version_id>/salvar/', subtitles.version_action, {'action': 'save'}, name='save_subtitle_version'),
    path('videos/<int:video_id>/legendas/<int:version_id>/entradas/nova/', subtitles.entry_save, name='create_subtitle_entry'),
    path('videos/<int:video_id>/legendas/<int:version_id>/entradas/<int:entry_id>/editar/', subtitles.edit_entry, name='edit_subtitle_entry'),
    path('videos/<int:video_id>/legendas/<int:version_id>/entradas/<int:entry_id>/salvar/', subtitles.entry_save, name='save_subtitle_entry'),
    path('videos/<int:video_id>/legendas/<int:version_id>/entradas/<int:entry_id>/confirmar-remocao/', subtitles.confirm_remove, name='confirm_remove_subtitle_entry'),
    path('videos/<int:video_id>/legendas/<int:version_id>/entradas/<int:entry_id>/remover/', subtitles.remove_entry, name='remove_subtitle_entry'),
    path('videos/<int:video_id>/marcacoes/nova/', annotations.create, name='create_marking'),
    path('videos/<int:video_id>/marcacoes/<int:marking_id>/editar/', annotations.edit, name='edit_marking'),
    path('videos/<int:video_id>/marcacoes/<int:marking_id>/salvar/', annotations.update, name='update_marking'),
    path('videos/<int:video_id>/marcacoes/<int:marking_id>/confirmar-remocao/', annotations.confirm_delete, name='confirm_delete_marking'),
    path('videos/<int:video_id>/marcacoes/<int:marking_id>/remover/', annotations.remove, name='remove_marking'),
    path('perfil/', views.profile, name='profile'),
    path('componentes/', views.components, name='components'),
]
