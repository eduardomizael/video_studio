from django.contrib import admin
from .models import MarcacaoTemporal


@admin.register(MarcacaoTemporal)
class MarkingAdmin(admin.ModelAdmin):
    list_display = ['title', 'video', 'start_ms', 'end_ms', 'updated_at']
    search_fields = ['title', 'video__title']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
