from django import forms
from .models import Adesao
from clientes_parceiros.models import ClientesParceiros, TipoRelacionamento

class AdesaoForm(forms.ModelForm):
    class Meta:
        model = Adesao
        fields = ['cliente', 'tese_credito_id', 'metodo_credito', 'data_inicio', 'perdcomp', 'ano_trimestre', 'periodo_apuracao',
                 'periodo_apuracao_um', 'codigo_receita', 'codigo_receita_denominacao', 'credito_original_utilizado',
                 'saldo', 'ativo', 'saldo_atual']
        widgets = {
            'cliente': forms.Select(attrs={
                'class': 'form-select',
            }),
            'tese_credito_id': forms.Select(attrs={
                'class': 'form-select',
            }),
            'metodo_credito': forms.Select(attrs={
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
            'ano_trimestre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ano/Trimestre (Ex: 2025/1)'
            }),
            'periodo_apuracao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Período de Apuração'
            }),
            'periodo_apuracao_um': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Período de Apuração 1'
            }),
            'codigo_receita': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código da Receita'
            }),
            'codigo_receita_denominacao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código Receita / Denominação'
            }),
            'credito_original_utilizado': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Crédito Original Utilizado',
                'step': '0.01'
            }),
            'saldo': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Saldo',
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
        
        # Filtra ESTRITAMENTE apenas clientes_parceiros com tipo_relacionamento=1 (Cliente) e ativos
        # Sem tentar buscar por nome ou outras tentativas
        try:
            # Filtra diretamente por id_tipo_relacionamento__id=1, que representa Cliente
            # Isso é mais direto e evita problemas se a referência não for encontrada
            self.fields['cliente'].queryset = ClientesParceiros.objects.filter(
                id_tipo_relacionamento__id=1,  # Filtra diretamente pelo ID do tipo de relacionamento
                ativo=True
            ).select_related('id_company_vinculada')
            
        except Exception as e:
            # Log do erro para diagnóstico
            print(f"Erro ao filtrar clientes: {e}")
            # Se ocorrer qualquer erro, não mostra nada
            self.fields['cliente'].queryset = ClientesParceiros.objects.none()
        
        # Personaliza o label para mostrar o nome da empresa cliente
        self.fields['cliente'].label_from_instance = lambda obj: f"{obj.id_company_vinculada.nome_fantasia or obj.id_company_vinculada.razao_social} ({obj.nome_referencia})"
