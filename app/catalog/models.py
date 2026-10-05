from pathlib import Path
import unicodedata

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .paths import resolve_media_path


def normalize_tag(name):
    return ' '.join(unicodedata.normalize('NFKC', name).split()).casefold()


class LocalMidia(models.Model):
    name = models.CharField('nome', max_length=150, unique=True)
    root_path = models.CharField('raiz absoluta no servidor', max_length=1000)
    active = models.BooleanField('ativo', default=True)

    class Meta:
        verbose_name = 'local de mídia'
        verbose_name_plural = 'locais de mídia'
        ordering = ['name', 'pk']

    def clean(self):
        super().clean()
        root = Path(self.root_path.strip())
        if not root.is_absolute():
            raise ValidationError({'root_path': 'Informe uma raiz absoluta no servidor.'})
        try:
            if root.exists() and not root.is_dir():
                raise ValidationError({'root_path': 'A raiz deve ser uma pasta.'})
            self.root_path = str(root.resolve())
        except (OSError, RuntimeError) as exc:
            raise ValidationError({'root_path': 'Não foi possível resolver a raiz.'}) from exc

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField('nome', max_length=100)
    normalized_name = models.CharField(max_length=300, unique=True, editable=False)
    color = models.CharField('cor', max_length=7, blank=True)

    class Meta:
        ordering = ['normalized_name', 'pk']

    def clean(self):
        super().clean()
        self.name = ' '.join(unicodedata.normalize('NFKC', self.name).split())
        self.normalized_name = normalize_tag(self.name)
        if not self.normalized_name:
            raise ValidationError({'name': 'Informe o nome da tag.'})
        if Tag.objects.filter(normalized_name=self.normalized_name).exclude(pk=self.pk).exists():
            raise ValidationError({'name': 'Já existe uma tag equivalente a este nome.'})

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Pessoa(models.Model):
    name = models.CharField('nome de exibição', max_length=150)
    notes = models.TextField('observações', blank=True)

    class Meta:
        verbose_name = 'pessoa'
        ordering = ['name', 'pk']

    def __str__(self):
        return f'{self.name} (#{self.pk})' if self.pk else self.name


class Video(models.Model):
    class FileStatus(models.TextChoices):
        AVAILABLE = 'available', 'Arquivo disponível'
        MISSING = 'missing', 'Arquivo não encontrado'
        UNREADABLE = 'unreadable', 'Sem acesso ao arquivo'

    title = models.CharField('título', max_length=200)
    description = models.TextField('descrição', blank=True)
    local_midia = models.ForeignKey(LocalMidia, on_delete=models.PROTECT, verbose_name='local de mídia')
    relative_path = models.CharField('caminho relativo', max_length=1000)
    path_key = models.CharField(max_length=1000, editable=False)
    duration_ms = models.PositiveBigIntegerField('duração em milissegundos', null=True, blank=True)
    duration_source = models.CharField(max_length=10, default='unknown', choices=[('unknown', 'Desconhecida'), ('automatic', 'Extraída'), ('manual', 'Manual')], editable=False)
    size_bytes = models.PositiveBigIntegerField(null=True, blank=True, editable=False)
    codec = models.CharField(max_length=80, blank=True, editable=False)
    width = models.PositiveIntegerField(null=True, blank=True, editable=False)
    height = models.PositiveIntegerField(null=True, blank=True, editable=False)
    inspection_status = models.CharField(max_length=12, default='pending', choices=[('pending', 'Não inspecionado'), ('ready', 'Inspecionado'), ('failed', 'Falha de inspeção'), ('unavailable', 'Inspeção indisponível')], editable=False)
    inspection_message = models.CharField(max_length=250, blank=True, editable=False)
    inspected_at = models.DateTimeField(null=True, blank=True, editable=False)
    thumbnail_key = models.CharField(max_length=64, blank=True, editable=False)
    thumbnail_relative_path = models.CharField('miniatura manual: caminho relativo', max_length=1000, blank=True)
    file_status = models.CharField(max_length=20, choices=FileStatus, default=FileStatus.MISSING, editable=False)
    tags = models.ManyToManyField(Tag, blank=True, related_name='videos')
    people = models.ManyToManyField(Pessoa, blank=True, related_name='videos', verbose_name='pessoas')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='created_videos', editable=False)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='updated_videos', editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        verbose_name = 'vídeo'
        ordering = ['-updated_at', '-pk']
        constraints = [
            models.UniqueConstraint(fields=['local_midia', 'path_key'], name='unique_video_media_reference'),
        ]

    def clean(self):
        super().clean()
        self.title = self.title.strip()
        if not self.title:
            raise ValidationError({'title': 'Informe o título do vídeo.'})
        if self.local_midia_id:
            try:
                _, self.relative_path, self.path_key = resolve_media_path(self.local_midia, self.relative_path)
            except ValidationError as exc:
                raise ValidationError({'relative_path': exc.messages}) from exc
            if Video.objects.filter(local_midia_id=self.local_midia_id, path_key=self.path_key).exclude(pk=self.pk).exists():
                raise ValidationError({'relative_path': 'Já existe um vídeo com essa referência de mídia.'})
            if self.thumbnail_relative_path:
                try:
                    target, normalized, _ = resolve_media_path(self.local_midia, self.thumbnail_relative_path)
                    if target.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp', '.gif'} or not target.is_file():
                        raise ValidationError('Selecione uma imagem JPG, PNG, WebP ou GIF existente no local de mídia.')
                    self.thumbnail_relative_path = normalized
                except ValidationError as exc:
                    raise ValidationError({'thumbnail_relative_path': exc.messages}) from exc

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title
