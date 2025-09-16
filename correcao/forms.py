from django import forms
from .models import TeseCredito



class TeseCreditoForm(forms.ModelForm):
    class Meta:
        model = TeseCredito
        fields = ['cod_origem', 'descricao', 'jurisprudencia']
        widgets = {
            'cod_origem': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código de origem'
            }),
            'descricao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descrição'
            }),
            'jurisprudencia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Jurisprudência'
            })
        }
        labels = {
            'id_tipo_tese': 'Tipo de Tese',
            'cod_origem': 'Código de Origem',
            'descricao': 'Descrição',
            'jurisprudencia': 'Jurisprudência'
        }
