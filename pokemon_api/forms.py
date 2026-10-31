from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Captura, Habilidade, Treinador


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


# ---------------------------------------------------------------------------
# Autenticação (semana 4)
# ---------------------------------------------------------------------------

class RegistroForm(UserCreationForm):
    """Cadastro de usuário: cria a conta de login e o perfil de treinador (1:1)."""

    nome = forms.CharField(label='Nome do treinador', max_length=100)
    cidade_natal = forms.CharField(label='Cidade natal', max_length=100, required=False)
    email = forms.EmailField(label='E-mail')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')
        labels = {'username': 'Nome de usuário'}

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Este e-mail já está cadastrado.')
        return email

    @transaction.atomic
    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.email = self.cleaned_data['email']
        usuario.first_name = self.cleaned_data['nome'][:150]
        usuario.save()
        Treinador.objects.create(
            usuario=usuario,
            nome=self.cleaned_data['nome'],
            cidade_natal=self.cleaned_data['cidade_natal'],
        )
        return usuario


class PerfilForm(forms.ModelForm):
    """Edição dos dados do próprio perfil (treinador + e-mail da conta)."""

    email = forms.EmailField(label='E-mail')

    class Meta:
        model = Treinador
        fields = ['nome', 'cidade_natal']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].initial = self.instance.usuario.email

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        outros = User.objects.filter(email__iexact=email).exclude(pk=self.instance.usuario_id)
        if outros.exists():
            raise ValidationError('Este e-mail já está em uso.')
        return email

    @transaction.atomic
    def save(self, commit=True):
        treinador = super().save(commit=commit)
        usuario = treinador.usuario
        usuario.email = self.cleaned_data['email']
        usuario.first_name = treinador.nome[:150]
        usuario.save()
        return treinador
