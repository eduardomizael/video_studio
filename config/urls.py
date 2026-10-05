from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('conta/', include('app.accounts.urls')),
    path('', include('app.studio.urls')),
]
