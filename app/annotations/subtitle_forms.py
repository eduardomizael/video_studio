from django import forms

from .forms import TimecodeField
from .models import SubtitleEntry, SubtitleVersion
from .srt import MAX_BYTES, parse_srt


class VersionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('auto_id', 'version_%s')
        super().__init__(*args, **kwargs)

    class Meta:
        model = SubtitleVersion
        fields = ['name', 'language']


class ImportForm(VersionForm):
    srt_file = forms.FileField(label='Arquivo SRT em UTF-8', help_text='Até 2 MB e 5.000 entradas. O arquivo é lido e não fica armazenado.')

    def __init__(self, *args, video, **kwargs):
        kwargs.setdefault('auto_id', 'import_%s')
        super().__init__(*args, **kwargs)
        self.instance.video = video

    def clean_srt_file(self):
        uploaded = self.cleaned_data['srt_file']
        self.entries = parse_srt(uploaded.read(MAX_BYTES + 1), self.instance.video.duration_ms)
        return uploaded


class EntryForm(forms.ModelForm):
    start_ms = TimecodeField(label='Início', initial=0)
    end_ms = TimecodeField(label='Fim')

    class Meta:
        model = SubtitleEntry
        fields = ['start_ms', 'end_ms', 'text']
        widgets = {'text': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, *args, version, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.version = version
