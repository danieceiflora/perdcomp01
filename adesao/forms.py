from django import forms
from django.utils.timezone import now
from .models import Adesao
from clientes_parceiros.models import ClientesParceiros, TipoRelacionamento

class AdesaoForm(forms.ModelForm):
    class Meta:
        model = Adesao
        fields = [
            'cliente', 'tese_credito_id', 'metodo_credito', 'data_inicio', 'perdcomp',
            'ano_trimestre', 'periodo_apuracao_credito', 'periodo_apuracao_debito', 'tipo_credito',
            'codigo_receita', 'codigo_receita_denominacao', 'valor_do_principal',
            'credito_original_utilizado', 'total',
            'saldo', 'ativo', 'saldo_atual'
        ]
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
            'periodo_apuracao_credito': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Período de Apuração Crédito'
            }),
            'periodo_apuracao_debito': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Período de Apuração Débito'
            }),
            'tipo_credito': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tipo de Crédito'
            }),
            'codigo_receita': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código da Receita'
            }),
            'codigo_receita_denominacao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código Receita / Denominação'
            }),
            'valor_do_principal': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Valor do Principal',
                'step': '0.01'
            }),
            'credito_original_utilizado': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Crédito Original Utilizado',
                'step': '0.01'
            }),
            'total': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Total',
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
        
        # Atualiza choices conforme fluxo
        if 'metodo_credito' in self.fields:
            self.fields['metodo_credito'].choices = [
                ('', 'Selecione...'),
                ('Pedido de compensação', 'Pedido de ressarcimento'),
                ('Pedido de restituição', 'Pedido de restituição'),
                ('Declaração de compensação', 'Declaração de compensação'),
                ('Declaração de compensação pagamento indevido', 'Declaração de compensação pagamento indevido'),
            ]

        # Campos condicionais não obrigatórios por padrão; validação no clean()
        # Saldo sempre obrigatório
        for fname in [
            'ano_trimestre', 'periodo_apuracao_credito', 'periodo_apuracao_debito',
            'tipo_credito', 'codigo_receita', 'codigo_receita_denominacao',
            'valor_do_principal', 'credito_original_utilizado', 'total'
        ]:
            if fname in self.fields:
                self.fields[fname].required = False
        
        # Campo saldo sempre obrigatório
        if 'saldo' in self.fields:
            self.fields['saldo'].required = True
        
        # Inicializações padrão
        if not self.instance.pk:
            self.fields['saldo_atual'].initial = self.initial.get('saldo', 0)
            if 'data_inicio' in self.fields and not self.fields['data_inicio'].initial:
                self.fields['data_inicio'].initial = now().date()
        else:
            self.fields['saldo_atual'].widget.attrs['readonly'] = True
            self.fields['saldo_atual'].help_text = 'Este campo é atualizado automaticamente pelos lançamentos'
        
        # Queryset de clientes (tipo Cliente / ativos)
        try:
            self.fields['cliente'].queryset = ClientesParceiros.objects.filter(
                id_tipo_relacionamento__id=1,
                ativo=True
            ).select_related('id_company_vinculada')
        except Exception as e:
            print(f"Erro ao filtrar clientes: {e}")
            self.fields['cliente'].queryset = ClientesParceiros.objects.none()
        
        # Label amigável
        self.fields['cliente'].label_from_instance = lambda obj: f"{obj.id_company_vinculada.nome_fantasia or obj.id_company_vinculada.razao_social} ({obj.nome_referencia})"

    def clean(self):
        cleaned = super().clean()
        metodo = cleaned.get('metodo_credito')

        if metodo == 'Pedido de compensação':  # Ressarcimento
            if not cleaned.get('ano_trimestre'):
                self.add_error('ano_trimestre', 'Informe o Ano/Trimestre.')
            if not cleaned.get('tipo_credito'):
                self.add_error('tipo_credito', 'Informe o Tipo de Crédito.')
        elif metodo == 'Pedido de restituição':
            if not cleaned.get('periodo_apuracao_credito'):
                self.add_error('periodo_apuracao_credito', 'Informe o Período de Apuração (Crédito).')
            if not cleaned.get('codigo_receita'):
                self.add_error('codigo_receita', 'Informe o Código da Receita.')
        elif metodo == 'Declaração de compensação':
            if cleaned.get('credito_original_utilizado') in (None, ''):
                self.add_error('credito_original_utilizado', 'Informe o Crédito Original Utilizado.')
        elif metodo == 'Declaração de compensação pagamento indevido':
            # Exigir: periodo_apuracao_credito, codigo_receita, codigo_receita_denominacao, periodo_apuracao_debito
            if not cleaned.get('periodo_apuracao_credito'):
                self.add_error('periodo_apuracao_credito', 'Informe o Período de Apuração (Crédito).')
            if not cleaned.get('codigo_receita'):
                self.add_error('codigo_receita', 'Informe o Código da Receita.')
            if not cleaned.get('codigo_receita_denominacao'):
                self.add_error('codigo_receita_denominacao', 'Informe o Código Receita / Denominação.')
            if not cleaned.get('periodo_apuracao_debito'):
                self.add_error('periodo_apuracao_debito', 'Informe o Período de Apuração (Débito).')

        return cleaned
