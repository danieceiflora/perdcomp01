from django import forms
from .models import Adesao
from clientes_parceiros.models import ClientesParceiros, TipoRelacionamento

class AdesaoForm(forms.ModelForm):
    class Meta:
        model = Adesao
        fields = ['cliente', 'tese_credito_id', 'data_inicio', 'perdcomp', 'saldo', 'free_rate', 'ativo', 'saldo_atual']
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
            'saldo_atual': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Saldo Atual',
                'step': '0.01'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Se for um novo objeto, inicializa o saldo_atual com o valor do saldo
        if not self.instance.pk:
            self.fields['saldo_atual'].initial = self.initial.get('saldo', 0)
            
        # Se estiver editando, torna o saldo_atual somente leitura
        else:
            self.fields['saldo_atual'].widget.attrs['readonly'] = True
            self.fields['saldo_atual'].help_text = 'Este campo é atualizado automaticamente pelos lançamentos'
        
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
