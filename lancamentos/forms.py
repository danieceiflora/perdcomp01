from django import forms
from django.forms import inlineformset_factory
from .models import Lancamentos, Anexos
from adesao.models import Adesao

class LancamentosForm(forms.ModelForm):
    metodo_escolhido = forms.ChoiceField(
        required=True,
        choices=[
            ('', 'Selecione o método...'),
            ('Pedido de ressarcimento', 'Pedido de ressarcimento'),
            ('Pedido de restituição', 'Pedido de restituição'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    # Campos dinâmicos (não persistem diretamente; serão copiados aos campos do model)
    lanc_total_credito_original_utilizado = forms.DecimalField(required=False, max_digits=15, decimal_places=2)
    lanc_debito = forms.DecimalField(required=False, max_digits=15, decimal_places=2)
    lanc_periodo_apuracao = forms.CharField(required=False, max_length=20)
    lanc_debito_r = forms.DecimalField(required=False, max_digits=15, decimal_places=2)
    lanc_periodo_apuracao_r = forms.CharField(required=False, max_length=20)
    lanc_total_r = forms.DecimalField(required=False, max_digits=15, decimal_places=2)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.data_lancamento:
            self.initial['data_lancamento'] = self.instance.data_lancamento.strftime('%Y-%m-%d')
        # Definir valor padrão para evitar validação de campo obrigatório
        if not self.instance.pk:
            self.initial['valor'] = 0

    class Meta:
        model = Lancamentos
        fields = ['id_adesao', 'metodo_escolhido', 'data_lancamento', 'valor', 'sinal', 'tipo', 'descricao',
                  'lanc_total_credito_original_utilizado', 'lanc_debito', 'lanc_periodo_apuracao',
                  'lanc_debito_r', 'lanc_periodo_apuracao_r', 'lanc_total_r',
                  'metodo', 'total', 'total_credito_original_utilizado', 'periodo_apuracao', 
                  'periodo_apuracao_r', 'debito', 'debito_r']
        widgets = {
            'id_adesao': forms.Select(attrs={'class': 'form-select'}),
            'data_lancamento': forms.DateInput(attrs={'class': 'form-control','type': 'date'}),
            'valor': forms.HiddenInput(),
            'sinal': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control','placeholder': 'Observações adicionais','rows': 3}),
        }

    def clean(self):
        cleaned = super().clean()
        metodo = (cleaned.get('metodo_escolhido') or '').lower()
        
        # Salvar o método escolhido no campo persistente
        cleaned['metodo'] = cleaned.get('metodo_escolhido', '')
        
        # Reset valor/sinal para recalcular
        cleaned['valor'] = None
        
        # Restituição: débito usando total_credito_original_utilizado
        if 'restitu' in metodo:
            total_cr = cleaned.get('lanc_total_credito_original_utilizado')
            if total_cr is None:
                self.add_error('lanc_total_credito_original_utilizado', 'Informe o valor.')
            else:
                cleaned['valor'] = float(total_cr)
                cleaned['sinal'] = '-'  # DÉBITO - diminui o saldo
                # Persistir dados originais
                cleaned['total_credito_original_utilizado'] = float(total_cr)
                cleaned['debito'] = cleaned.get('lanc_debito') or 0
                cleaned['periodo_apuracao'] = cleaned.get('lanc_periodo_apuracao') or ''
                
        # Ressarcimento: débito usando total_r (diminui o saldo disponível)
        elif 'ressarc' in metodo:
            total_r = cleaned.get('lanc_total_r')
            if total_r is None:
                self.add_error('lanc_total_r', 'Informe o total.')
            else:
                cleaned['valor'] = float(total_r)
                cleaned['sinal'] = '-'  # DÉBITO - diminui o saldo (recurso usado)
                # Persistir dados originais
                cleaned['total'] = float(total_r)
                cleaned['debito_r'] = cleaned.get('lanc_debito_r') or 0
                cleaned['periodo_apuracao_r'] = cleaned.get('lanc_periodo_apuracao_r') or ''
        
        if cleaned.get('valor') in (None, 0):
            self.add_error('valor', 'Valor inválido ou ausente.')
        
        return cleaned

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