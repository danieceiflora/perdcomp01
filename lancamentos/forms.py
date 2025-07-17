from django import forms
from django.forms import inlineformset_factory
from .models import Lancamentos, Anexos
from adesao.models import Adesao

class LancamentosForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Formatando a data para o formato esperado pelo input type="date" (yyyy-mm-dd)
        if self.instance.pk and self.instance.data_lancamento:
            self.initial['data_lancamento'] = self.instance.data_lancamento.strftime('%Y-%m-%d')
    
    class Meta:
        model = Lancamentos
        fields = ['id_adesao', 'data_lancamento', 'valor', 'sinal', 'tipo', 'observacao']
        widgets = {
            'id_adesao': forms.Select(attrs={
                'class': 'form-select',
            }),
            'data_lancamento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'valor': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Valor do Lançamento',
                'step': '0.01'
            }),
            'sinal': forms.Select(attrs={
                'class': 'form-select',
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select',
            }),
            'observacao': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Observações adicionais',
                'rows': 3
            }),
        }

class AnexosForm(forms.ModelForm):
    class Meta:
        model = Anexos
        fields = ['arquivo', 'nome_anexo', 'descricao']
        widgets = {
            'arquivo': forms.FileInput(attrs={
                'class': 'form-control',
            }),
            'nome_anexo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do anexo'
            }),
            'descricao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descrição do conteúdo'
            }),
        }

# Cria um FormSet para gerenciar múltiplos anexos
AnexosFormSet = inlineformset_factory(
    Lancamentos, 
    Anexos, 
    form=AnexosForm, 
    extra=1, 
    can_delete=True
)