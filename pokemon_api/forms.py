from django import forms

from .models import Pokemon


def texto_para_lista(texto):
    return [item.strip().lower() for item in texto.split(',') if item.strip()]


class PokemonForm(forms.ModelForm):
    id_pokemon = forms.IntegerField(
        label='Número da Pokédex',
        min_value=1,
        widget=forms.NumberInput(attrs={'placeholder': 'Ex: 1'}),
    )
    tipos = forms.CharField(
        label='Tipos',
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: grass, poison'}),
        help_text='Separe os tipos por vírgula.',
    )
    habilidades = forms.CharField(
        label='Habilidades',
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: overgrow, chlorophyll'}),
        help_text='Separe as habilidades por vírgula.',
    )
    hp = forms.IntegerField(label='HP', min_value=0, initial=0)
    ataque = forms.IntegerField(label='Ataque', min_value=0, initial=0)
    defesa = forms.IntegerField(label='Defesa', min_value=0, initial=0)
    velocidade = forms.IntegerField(label='Velocidade', min_value=0, initial=0)

    class Meta:
        model = Pokemon
        fields = [
            'nome', 'id_pokemon', 'treinador', 'tipos', 'habilidades',
            'altura', 'peso', 'hp', 'ataque', 'defesa', 'velocidade',
            'sprite_url', 'observacoes', 'capturado', 'favorito',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Ex: Bulbasaur'}),
            'altura': forms.TextInput(attrs={'placeholder': 'Ex: 0.7 m'}),
            'peso': forms.TextInput(attrs={'placeholder': 'Ex: 6.9 kg'}),
            'sprite_url': forms.URLInput(),
            'observacoes': forms.Textarea(attrs={
                'placeholder': 'Escreva notas sobre táticas de batalha, onde foi encontrado, etc.',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['treinador'].empty_label = 'Sem treinador'
        for campo in ('tipos', 'habilidades'):
            valor = self.initial.get(campo)
            if isinstance(valor, list):
                self.initial[campo] = ', '.join(valor)

    def clean_tipos(self):
        tipos = texto_para_lista(self.cleaned_data['tipos'])
        if not tipos:
            raise forms.ValidationError('Informe ao menos um tipo.')
        return tipos

    def clean_habilidades(self):
        return texto_para_lista(self.cleaned_data['habilidades'])
