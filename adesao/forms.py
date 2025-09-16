from django import forms
from django.utils.timezone import now
from .models import Adesao
from clientes_parceiros.models import ClientesParceiros

import re

MMYYYY_REGEX = re.compile(r'^(0[1-9]|1[0-2])/\d{4}$')

class AdesaoForm(forms.ModelForm):
    
    class Meta:
        model = Adesao
        fields = [
            'cliente', 'tese_credito_id', 'metodo_credito', 'data_inicio', 'perdcomp','ano','trimestre',
            'periodo_apuracao_credito', 'periodo_apuracao_debito', 'tipo_credito',
            'codigo_receita', 'codigo_receita_denominacao', 'valor_do_principal',
            'credito_original_utilizado', 'total',
            'saldo', 'saldo_atual', 'selic_acumulada', 'valor_correcao', 'valor_total_corrigido',
            'data_arrecadacao'
        ]
        widgets = {
            'cliente': forms.Select(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
            }),
            'tese_credito_id': forms.Select(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
            }),
            'metodo_credito': forms.Select(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
            }),
            'data_inicio': forms.DateInput(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                'type': 'date'
            }),
            'perdcomp': forms.TextInput(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                'placeholder': 'Número do PERDCOMP'
            }),
            'ano': forms.TextInput(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                'placeholder': 'Ano'
            }),
            'trimestre': forms.Select(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                'placeholder': 'Trimestre'
            }),
            'periodo_apuracao_credito': forms.TextInput(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                'placeholder': 'mm/aaaa'
            }),
            'periodo_apuracao_debito': forms.TextInput(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                'placeholder': 'mm/aaaa'
            }),
            'tipo_credito': forms.TextInput(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                'placeholder': 'Tipo de Crédito'
            }),
            'codigo_receita': forms.TextInput(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                'placeholder': 'Código da Receita'
            }),
            'codigo_receita_denominacao': forms.TextInput(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                'placeholder': 'Código Receita / Denominação'
            }),
            'valor_do_principal': forms.NumberInput(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                'placeholder': 'Valor do Principal',
                'step': '0.01'
            }),
            'credito_original_utilizado': forms.NumberInput(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                'placeholder': 'Crédito Original Utilizado',
                'step': '0.01'
            }),
            'total': forms.NumberInput(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                'placeholder': 'Total',
                'step': '0.01'
            }),
            'saldo': forms.NumberInput(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 pl-8',
                'placeholder': 'Saldo',
                'step': '0.01'
            }),
          
            'saldo_atual': forms.NumberInput(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                'placeholder': 'Saldo Atual',
                'step': '0.01'
            }),
            'selic_acumulada': forms.NumberInput(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                'placeholder': 'SELIC Acumulada (%)',
                'step': '0.01'
            }),
            'valor_correcao': forms.NumberInput(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                'placeholder': 'Valor da Correção',
                'step': '0.01'
            }),
            'valor_total_corrigido': forms.NumberInput(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                'placeholder': 'Valor Total Corrigido',
                'step': '0.01'
            })
            ,
            'data_arrecadacao': forms.DateInput(attrs={
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                'type': 'date'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    # Atualiza choices conforme fluxo
        if 'metodo_credito' in self.fields:
            base_choices = [
                ('', 'Selecione...'),
                ('Pedido de ressarcimento', 'Pedido de ressarcimento'),
                ('Pedido de restituição', 'Pedido de restituição'),
                ('Declaração de compensação pagamento indevido', 'Declaração de compensação pagamento indevido'),
            ]
            # Se edição (instance.pk), permitir eventualmente futura lógica diferente; por ora igual
            if self.instance.pk:
                self.fields['metodo_credito'].choices = base_choices
            else:
                self.fields['metodo_credito'].choices = base_choices

        # Campos condicionais não obrigatórios por padrão; validação no clean()
        # Saldo sempre obrigatório
        for fname in [
            'periodo_apuracao_credito', 'periodo_apuracao_debito',
            'tipo_credito', 'codigo_receita', 'codigo_receita_denominacao',
            'valor_do_principal', 'credito_original_utilizado', 'total', 'ano'
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
        

        # Label amigável
        self.fields['cliente'].label_from_instance = lambda obj: f"{obj.id_company_vinculada.nome_fantasia or obj.id_company_vinculada.razao_social} ({obj.nome_referencia})"

    def clean(self):
        cleaned = super().clean()
        metodo = cleaned.get('metodo_credito')

        if metodo == 'Pedido de compensação':  # Ressarcimento
            if not cleaned.get('ano'):
                self.add_error('ano', 'Informe o Ano.')
            if not cleaned.get('trimestre'):
                self.add_error('trimestre', 'Informe o Trimestre.')
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

    # clean_ano_trimestre não necessário: DateField já converte usando input_formats

    def clean_periodo_apuracao_credito(self):
        v = self.cleaned_data.get('periodo_apuracao_credito')
        if not v:
            return v
        if not MMYYYY_REGEX.match(v):
            raise forms.ValidationError('Formato deve ser mm/aaaa.')
        return v

    def clean_periodo_apuracao_debito(self):
        v = self.cleaned_data.get('periodo_apuracao_debito')
        if not v:
            return v
        if not MMYYYY_REGEX.match(v):
            raise forms.ValidationError('Formato deve ser mm/aaaa.')
        return v
