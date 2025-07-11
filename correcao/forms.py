from django import forms
from .models import Correcao

class CorrecaoForm(forms.ModelForm):
    class Meta:
        model = Correcao
        fields = ['cod_origem', 'descricao', 'fonte_correcao']
        widgets = {
            'cod_origem': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código de origem'
            }),
            'descricao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descrição'
            }),
            'fonte_correcao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Fonte da correção'
            }),
        }
        labels = {
            'cod_origem': 'Código de Origem',
            'descricao': 'Descrição',
            'fonte_correcao': 'Fonte da Correção',
        }
