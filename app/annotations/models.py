from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class MarcacaoTemporal(models.Model):
    video = models.ForeignKey('catalog.Video', on_delete=models.CASCADE, related_name='markings')
    title = models.CharField('título', max_length=200)
    start_ms = models.PositiveBigIntegerField('início em milissegundos')
    end_ms = models.PositiveBigIntegerField('fim em milissegundos', null=True, blank=True)
    tags = models.ManyToManyField('catalog.Tag', blank=True, related_name='markings')
    people = models.ManyToManyField('catalog.Pessoa', blank=True, related_name='markings', verbose_name='pessoas')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='created_markings', editable=False)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='updated_markings', editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'marcação temporal'
        verbose_name_plural = 'marcações temporais'
        ordering = ['start_ms', 'pk']
        indexes = [models.Index(fields=['video', 'start_ms'])]
        constraints = [models.CheckConstraint(condition=models.Q(end_ms__isnull=True) | models.Q(end_ms__gte=models.F('start_ms')), name='marking_end_not_before_start')]

    def clean(self):
        super().clean()
        self.title = self.title.strip()
        errors = {}
        if not self.title:
            errors['title'] = 'Informe o título da marcação.'
        if self.start_ms is not None and self.end_ms is not None and self.end_ms < self.start_ms:
            errors['end_ms'] = 'O fim não pode ser anterior ao início.'
        if self.video_id and self.video.duration_ms is not None:
            for field in ['start_ms', 'end_ms']:
                value = getattr(self, field)
                if value is not None and value > self.video.duration_ms:
                    errors[field] = 'O tempo ultrapassa a duração conhecida do vídeo.'
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.title


class SubtitleVersion(models.Model):
    video = models.ForeignKey('catalog.Video', on_delete=models.CASCADE, related_name='subtitle_versions')
    name = models.CharField('nome da versão', max_length=200)
    language = models.CharField('idioma (opcional)', max_length=40, blank=True)
    active = models.BooleanField(default=False)
    source = models.CharField('origem', max_length=20, default='srt', editable=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='+', editable=False)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='+', editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        constraints = [models.UniqueConstraint(fields=['video'], condition=models.Q(active=True), name='one_active_subtitle_version')]

    def clean(self):
        self.name = self.name.strip()
        if not self.name:
            raise ValidationError({'name': 'Informe o nome da versão.'})

    def __str__(self):
        return self.name


class SubtitleEntry(models.Model):
    version = models.ForeignKey(SubtitleVersion, on_delete=models.CASCADE, related_name='entries')
    start_ms = models.PositiveBigIntegerField('início')
    end_ms = models.PositiveBigIntegerField('fim')
    text = models.TextField('texto', max_length=10000)
    order = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ['start_ms', 'order', 'pk']
        constraints = [models.CheckConstraint(condition=models.Q(end_ms__gt=models.F('start_ms')), name='subtitle_end_after_start')]

    def clean(self):
        errors = {}
        self.text = self.text.strip()
        if not self.text:
            errors['text'] = 'Informe o texto da legenda.'
        if self.start_ms is not None and self.end_ms is not None and self.end_ms <= self.start_ms:
            errors['end_ms'] = 'O fim deve ser posterior ao início.'
        if self.version_id and self.version.video.duration_ms is not None:
            for field in ['start_ms', 'end_ms']:
                if getattr(self, field) is not None and getattr(self, field) > self.version.video.duration_ms:
                    errors[field] = 'O tempo ultrapassa a duração conhecida do vídeo.'
        if errors:
            raise ValidationError(errors)
