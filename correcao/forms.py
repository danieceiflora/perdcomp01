from django import forms
from .models import tipoTese, TeseCredito

class tipoTeseForm(forms.ModelForm):
    class Meta:
        model = tipoTese
        fields = ['descricao', 'periodicidade']
        widgets = {
            'descricao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descrição do tipo de tese'
            }),
            'periodicidade': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Selecione'
            }),  
        }
        labels = {
            'descricao': 'Descrição',
            'periodicidade': 'Periodicidade'
        }

class TeseCreditoForm(forms.ModelForm):
    class Meta:
        model = TeseCredito
        fields = ['id_tipo_tese', 'cod_origem', 'descricao', 'jurisprudencia']
        widgets = {
            'id_tipo_tese': forms.Select(attrs={
                'class': 'form-select',
            }),
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
