from django import forms
from .models import Adesao
from clientes_parceiros.models import ClientesParceiros, TipoRelacionamento

class AdesaoForm(forms.ModelForm):
    class Meta:
        model = Adesao
        fields = ['cliente', 'tese_credito_id', 'data_inicio', 'perdcomp', 'saldo', 'free_rate', 'ativo']
        widgets = {
            'cliente': forms.Select(attrs={
                'class': 'form-select',
            }),
            'tese_credito_id': forms.Select(attrs={
                'class': 'form-select',
            }),
            'data_inicio': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'perdcomp': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número do PERDCOMP'
            }),
            'saldo': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Saldo',
                'step': '0.01'
            }),
            'free_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Free Rate',
                'step': '0.01'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtra apenas clientes_parceiros com tipo_relacionamento=1 (Cliente) e ativos
        try:
            tipo_cliente = TipoRelacionamento.objects.get(pk=1)  # Tipo Cliente (id=1)
            self.fields['cliente'].queryset = ClientesParceiros.objects.filter(
                id_tipo_relacionamento=tipo_cliente,
                ativo=True
            ).select_related('id_company_vinculada')
        except TipoRelacionamento.DoesNotExist:
            # Se não encontrar o tipo 1, mostra uma lista vazia ou todos os clientes
            self.fields['cliente'].queryset = ClientesParceiros.objects.filter(ativo=True)
        
        # Personaliza o label para mostrar o nome da empresa cliente
        self.fields['cliente'].label_from_instance = lambda obj: f"{obj.id_company_vinculada.nome_fantasia or obj.id_company_vinculada.razao_social} ({obj.nome_referencia})"
