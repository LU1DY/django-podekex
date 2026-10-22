from django import forms
from django.core.exceptions import ValidationError

from .models import Captura, Habilidade


class HabilidadeForm(forms.ModelForm):
    """CRUD da entidade Habilidade (segunda entidade do N:N)."""

    class Meta:
        model = Habilidade
        fields = ['nome', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Ex: static', 'maxlength': 100}),
            'descricao': forms.Textarea(attrs={
                'placeholder': 'Explique o que essa habilidade faz em batalha...',
                'rows': 5,
            }),
        }
        error_messages = {
            'nome': {
                'required': 'Informe o nome da habilidade.',
                'unique': 'Já existe uma habilidade com esse nome.',
            },
        }

    def clean_nome(self):
        nome = ' '.join(self.cleaned_data['nome'].split())
        repetida = Habilidade.objects.filter(nome__iexact=nome).exclude(pk=self.instance.pk)
        if repetida.exists():
            raise ValidationError('Já existe uma habilidade com esse nome.')
        return nome


class CapturaForm(forms.ModelForm):
    """Ficha de captura (1:1 com Pokémon), exibida dentro do formulário do Pokémon."""

    class Meta:
        model = Captura
        fields = ['apelido', 'nivel', 'pokebola', 'local', 'data_encontro']
        widgets = {
            'apelido': forms.TextInput(attrs={'placeholder': 'Ex: Pika', 'maxlength': 50}),
            'nivel': forms.NumberInput(attrs={'placeholder': '1 a 100', 'min': 1, 'max': 100}),
            'local': forms.TextInput(attrs={'placeholder': 'Ex: Floresta de Viridian', 'maxlength': 100}),
            'data_encontro': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }
        error_messages = {
            'nivel': {
                'invalid': 'Informe o nível como número inteiro.',
                'min_value': 'O nível mínimo é 1.',
                'max_value': 'O nível máximo é 100.',
            },
            'data_encontro': {'invalid': 'Informe uma data válida.'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pokebola'].choices = [('', 'Não informada'), *Captura.Pokebola.choices]

    def tem_dados(self):
        """Verdadeiro se o usuário preencheu algum campo (use depois de is_valid)."""
        return any(valor not in (None, '') for valor in self.cleaned_data.values())
