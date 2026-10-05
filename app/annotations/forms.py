from django import forms

from .models import MarcacaoTemporal
from .timecodes import format_timecode, parse_timecode


class TimecodeField(forms.CharField):
    def to_python(self, value):
        value = super().to_python(value)
        return parse_timecode(value) if value else None

    def prepare_value(self, value):
        return format_timecode(value) if isinstance(value, int) else value


class MarkingForm(forms.ModelForm):
    start_ms = TimecodeField(label='Início', help_text='MM:SS.mmm ou HH:MM:SS.mmm', initial=0)
    end_ms = TimecodeField(label='Fim (opcional)', required=False, help_text='Deixe vazio para uma marcação pontual.')

    class Meta:
        model = MarcacaoTemporal
        fields = ['title', 'start_ms', 'end_ms', 'tags', 'people']
        widgets = {'tags': forms.SelectMultiple(attrs={'size': 4}), 'people': forms.SelectMultiple(attrs={'size': 4})}
        help_texts = {'tags': 'Tags deste trecho, independentes das tags do vídeo.', 'people': 'Pessoas presentes neste ponto/intervalo. Ctrl/Cmd permite selecionar vários cadastros.'}

    def __init__(self, *args, video, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.video = video
