from django.contrib import admin
from .models import LocalMidia, Pessoa, Tag, Video


@admin.register(LocalMidia)
class LocalMidiaAdmin(admin.ModelAdmin):
    list_display = ['name', 'root_path', 'active']
    list_filter = ['active']
    search_fields = ['name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(Pessoa)
class PessoaAdmin(admin.ModelAdmin):
    search_fields = ['name', 'notes']


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'local_midia', 'file_status', 'updated_at']
    search_fields = ['title', 'description']
    readonly_fields = ['file_status', 'created_by', 'updated_by', 'created_at', 'updated_at', 'duration_ms', 'duration_source', 'inspection_status', 'inspection_message', 'inspected_at', 'codec', 'width', 'height', 'size_bytes', 'thumbnail_key']
    filter_horizontal = ['tags', 'people']

    def has_add_permission(self, request):
        return False  # Registration goes through the validated catalog service.

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
