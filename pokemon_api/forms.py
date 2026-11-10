from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Pokemon, Regiao, Treinador


class PokemonForm(forms.ModelForm):
    """Edição do que é do treinador; os dados da espécie vêm da PokéAPI."""

    class Meta:
        model = Pokemon
        fields = ['observacoes', 'capturado', 'favorito']
        widgets = {'observacoes': forms.Textarea(attrs={'rows': 4})}


class RegistroForm(UserCreationForm):
    """Cria a conta de login e o perfil de treinador (1:1)."""

    nome = forms.CharField(label='Nome do treinador', max_length=100)
    cidade_natal = forms.CharField(label='Cidade natal', max_length=100, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username',)
        labels = {'username': 'Nome de usuário'}

    def save(self, commit=True):
        usuario = super().save(commit=commit)
        Treinador.objects.create(
            usuario=usuario,
            nome=self.cleaned_data['nome'],
            cidade_natal=self.cleaned_data['cidade_natal'],
        )
        return usuario


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Treinador
        fields = ['nome', 'cidade_natal']


class ConsultaForm(forms.Form):
    """Filtros da tela de consultas (GET). Todos opcionais."""

    q = forms.CharField(label='Nome ou número', max_length=100, required=False)
    tipo = forms.CharField(label='Tipo', max_length=30, required=False)
    regiao = forms.ModelChoiceField(
        label='Região', queryset=Regiao.objects.order_by('numero_inicial'),
        required=False, empty_label='Todas as regiões',
    )
    data_inicio = forms.DateField(
        label='Adicionado de', required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    data_fim = forms.DateField(
        label='até', required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
