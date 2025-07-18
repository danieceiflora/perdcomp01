from django import forms
from .models import Correcao, tipoTese, TeseCredito

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

class tipoTeseForm(forms.ModelForm):
    class Meta:
        model = tipoTese
        fields = ['descricao']
        widgets = {
            'descricao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descrição do tipo de tese'
            }),
        }
        labels = {
            'descricao': 'Descrição',
        }

class TeseCreditoForm(forms.ModelForm):
    class Meta:
        model = TeseCredito
        fields = ['id_correcao', 'id_tipo_tese', 'cod_origem', 'descricao', 'jurisprudencia', 'corrige',]
        widgets = {
            'id_correcao': forms.Select(attrs={
                'class': 'form-select',
            }),
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
            }),
            'corrige': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'id_correcao': 'Correção',
            'id_tipo_tese': 'Tipo de Tese',
            'cod_origem': 'Código de Origem',
            'descricao': 'Descrição',
            'jurisprudencia': 'Jurisprudência',
            'corrige': 'Aplicar Correção'
        }
