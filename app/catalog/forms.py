from django import forms
from django.core.exceptions import ValidationError
import unicodedata

from .models import LocalMidia, Pessoa, Tag, Video


class VideoForm(forms.ModelForm):
    new_tags = forms.CharField(label='Novas tags', required=False, help_text='Separe por vírgulas. Termos equivalentes reutilizam a tag existente.')
    new_person_name = forms.CharField(label='Cadastrar e associar uma nova pessoa', max_length=150, required=False)
    new_person_notes = forms.CharField(label='Observações da nova pessoa', required=False, widget=forms.Textarea(attrs={'rows': 2}), max_length=2000)

    class Meta:
        model = Video
        fields = ['title', 'description', 'local_midia', 'relative_path', 'duration_ms', 'thumbnail_relative_path', 'tags', 'people']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'tags': forms.SelectMultiple(attrs={'size': 6}),
            'people': forms.SelectMultiple(attrs={'size': 6}),
        }
        help_texts = {
            'relative_path': 'Exemplo: entrevistas/episodio-08.mp4. O arquivo deve estar no servidor; não há upload.',
            'tags': 'Selecione as tags existentes. Ctrl/Cmd permite selecionar ou remover vários itens.',
            'people': 'Selecione cadastros existentes pelo nome e ID. Homônimos são permitidos.',
            'duration_ms': 'Opcional. 60000 = 1 minuto. Um valor corrigido manualmente tem prioridade sobre a extração.',
            'thumbnail_relative_path': 'Opcional. Imagem já existente no mesmo local de mídia; não há upload. Deixe vazio para usar o frame extraído.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['local_midia'].queryset = LocalMidia.objects.filter(active=True)
        self.fields['tags'].queryset = Tag.objects.all()
        self.fields['people'].queryset = Pessoa.objects.all()

    def clean_new_tags(self):
        names = [' '.join(unicodedata.normalize('NFKC', name).split()) for name in self.cleaned_data['new_tags'].split(',') if name.strip()]
        if any(len(name) > 100 for name in names):
            raise ValidationError('Cada tag deve ter no máximo 100 caracteres.')
        return names

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('new_person_notes') and not cleaned.get('new_person_name'):
            self.add_error('new_person_name', 'Informe o nome para cadastrar a pessoa com estas observações.')
        return cleaned
