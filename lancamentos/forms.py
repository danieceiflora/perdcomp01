from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import Lancamentos, Anexos
from adesao.models import Adesao

class LancamentosForm(forms.ModelForm):
    metodo_escolhido = forms.ChoiceField(
        required=True,
        choices=[
            ('', 'Selecione o método...'),
            ('Declaração de compensação', 'Declaração de compensação'),
            ('Crédito em conta', 'Crédito em conta'),
        ],
        widget=forms.Select(attrs={'class': 'input w-full'})
    )
    # Campos dinâmicos (não persistem diretamente; serão copiados aos campos do model)
    lanc_total_credito_original_utilizado = forms.DecimalField(
        required=False, 
        max_digits=15, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'input w-full', 'step': '0.01', 'placeholder': '0,00'}),
        label='Total Crédito Original Utilizado'
    )
    
    lanc_total_debitos_documento = forms.DecimalField(
        required=False,
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'input w-full', 'step': '0.01', 'placeholder': '0,00'}),
        label='Total dos Débitos deste Documento'
    )
    
    lanc_periodo_apuracao = forms.CharField(
        required=False, 
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'input w-full', 'placeholder': 'Ex: 01/2025'}),
        label='Período de Apuração'
    )
    
    lanc_data_credito = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'input w-full', 'type': 'date'}),
        input_formats=['%Y-%m-%d', '%d/%m/%Y'],
        label='Data do Crédito'
    )
    
    lanc_valor_credito_em_conta = forms.DecimalField(
        required=False,
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'input w-full', 'step': '0.01', 'placeholder': '0,00'}),
        label='Valor do Crédito em Conta'
    )
    
    # Campo para exibir o saldo atual da adesão selecionada (somente leitura)
    saldo_atual_adesao = forms.DecimalField(
        required=False,
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'input w-full bg-muted/30 dark:bg-muted/20 text-foreground dark:text-foreground read-only:opacity-90',
            'readonly': True,
            'placeholder': 'Selecione uma adesão...'
        }),
        label='Saldo Atual da Adesão'
    )

    # Campos de aprovação
    aprovado = forms.TypedChoiceField(
        choices=[(True, 'Sim'), (False, 'Não')],
        coerce=lambda v: True if v in (True, 'True', 'true', '1', 1, 'on') else False,
        required=False,
        widget=forms.Select(attrs={'class': 'input w-full'})
    )
    data_aprovacao = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'input w-full'}),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S']
    )
    observacao_aprovacao = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'input w-full', 'rows': 3, 'placeholder': 'Observações sobre a aprovação (opcional)'})
    )
    
    # Campos de recibo de protocolo
    numero_controle = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'input w-full',
            'placeholder': 'Número de controle do recibo'
        }),
        label='Número de Controle'
    )
    chave_seguranca_serpro = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'input w-full',
            'placeholder': 'Chave de segurança SERPRO'
        }),
        label='Chave de Segurança SERPRO'
    )
    status = forms.ChoiceField(
        required=False,
        choices=[
            ('solicitado', 'Solicitado'),
            ('protocolado', 'Protocolado'),
        ],
        initial='solicitado',
        widget=forms.Select(attrs={'class': 'input w-full'}),
        label='Status do Controle'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.data_lancamento:
            self.initial['data_lancamento'] = self.instance.data_lancamento.strftime('%Y-%m-%d')
        if self.instance.pk and self.instance.data_credito:
            self.initial['lanc_data_credito'] = self.instance.data_credito
        if self.instance.pk and self.instance.valor_credito_em_conta is not None:
            self.initial['lanc_valor_credito_em_conta'] = self.instance.valor_credito_em_conta
        # Definir valor padrão para evitar validação de campo obrigatório
        if not self.instance.pk:
            self.initial['valor'] = 0
            # Definir status padrão como 'solicitado' para novos lançamentos
            if 'status' not in self.initial:
                self.initial['status'] = 'solicitado'

    class Meta:
        model = Lancamentos
        fields = ['id_adesao', 'metodo_escolhido', 'data_lancamento', 'valor', 'descricao', 'codigo_guia',
                  'lanc_total_credito_original_utilizado', 'lanc_total_debitos_documento', 'lanc_periodo_apuracao',
                  'lanc_data_credito', 'lanc_valor_credito_em_conta',
                  'metodo', 'total', 'total_credito_original_utilizado', 'total_debitos_documento', 'descricao_debitos',
                  'periodo_apuracao', 'data_credito', 'valor_credito_em_conta',
                  'aprovado', 'data_aprovacao', 'observacao_aprovacao',
                  'numero_controle', 'chave_seguranca_serpro', 'status']
        widgets = {
            'id_adesao': forms.Select(attrs={'class': 'input w-full'}),
            'data_lancamento': forms.DateInput(attrs={'class': 'input w-full','type': 'date'}),
            'valor': forms.HiddenInput(),
            'descricao': forms.Textarea(attrs={'class': 'input w-full','placeholder': 'Observações adicionais','rows': 3}),
            'codigo_guia': forms.TextInput(attrs={'class': 'input w-full', 'placeholder': 'Informe o código da guia'}),
            'aprovado': forms.Select(choices=[(True, 'Sim'), (False, 'Não')], attrs={'class': 'input w-full'}),
            'data_aprovacao': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'input w-full'}),
            'observacao_aprovacao': forms.Textarea(attrs={'class': 'input w-full', 'rows': 3}),
            'data_credito': forms.HiddenInput(),
            'valor_credito_em_conta': forms.HiddenInput(),
            'total_debitos_documento': forms.HiddenInput(),
            'descricao_debitos': forms.HiddenInput(),
        }

    def add_error_classes(self):
        """Append error style classes to fields with validation errors."""
        error_cls = ' border-destructive focus-visible:ring-destructive'
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.HiddenInput):
                continue
            base = field.widget.attrs.get('class', '')
            if 'input' not in base:
                base = 'input w-full ' + base
            if self[name].errors and error_cls not in base:
                field.widget.attrs['class'] = base + error_cls
            else:
                field.widget.attrs['class'] = base.strip()

    def __init__(self, *args, **kwargs):  # move after Meta to keep overrides
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.data_lancamento:
            self.initial['data_lancamento'] = self.instance.data_lancamento.strftime('%Y-%m-%d')
        if self.instance.pk and self.instance.data_credito:
            self.initial['lanc_data_credito'] = self.instance.data_credito
        if self.instance.pk and self.instance.valor_credito_em_conta is not None:
            self.initial['lanc_valor_credito_em_conta'] = self.instance.valor_credito_em_conta
        if not self.instance.pk:
            self.initial['valor'] = 0
        # Apply error classes after validation data present
        self.add_error_classes()

    def clean(self):
        cleaned = super().clean()
        metodo = (cleaned.get('metodo_escolhido') or '').lower()
        
        # Salvar o método escolhido no campo persistente
        cleaned['metodo'] = cleaned.get('metodo_escolhido', '')
        
        # Reset valor/sinal para recalcular
        cleaned['valor'] = None
        cleaned['data_credito'] = None
        cleaned['valor_credito_em_conta'] = None
        cleaned['total_debitos_documento'] = None
        cleaned['descricao_debitos'] = None
        
        # Declaração de Compensação: usar total_debitos_documento
        if 'compensacao' in metodo or 'compensação' in metodo:
            total_cred = cleaned.get('lanc_total_credito_original_utilizado')
            total_deb = cleaned.get('lanc_total_debitos_documento')
            periodo = cleaned.get('lanc_periodo_apuracao')
            
            if not total_deb:
                self.add_error('lanc_total_debitos_documento', 'Total dos débitos é obrigatório para Declaração de Compensação.')
            if not periodo:
                self.add_error('lanc_periodo_apuracao', 'Período de apuração é obrigatório para Declaração de Compensação.')
            
            if total_deb:
                cleaned['total_debitos_documento'] = float(total_deb)
                cleaned['valor'] = float(total_deb)
                cleaned['sinal'] = '-'
            
            if total_cred:
                cleaned['total_credito_original_utilizado'] = float(total_cred)
            
            if periodo:
                cleaned['periodo_apuracao'] = periodo

        # Crédito em conta
        elif 'credito' in metodo and 'conta' in metodo:
            data_credito = cleaned.get('lanc_data_credito')
            valor_credito = cleaned.get('lanc_valor_credito_em_conta')
            if not data_credito:
                self.add_error('lanc_data_credito', 'Informe a data do crédito.')
            else:
                cleaned['data_credito'] = data_credito
            if valor_credito in (None, ''):
                self.add_error('lanc_valor_credito_em_conta', 'Informe o valor creditado.')
            else:
                try:
                    cleaned['valor'] = float(valor_credito)
                    cleaned['valor_credito_em_conta'] = float(valor_credito)
                    cleaned['sinal'] = '+'
                except (TypeError, ValueError):
                    self.add_error('lanc_valor_credito_em_conta', 'Valor inválido informado.')
        
        if cleaned.get('valor') in (None, 0):
            self.add_error('valor', 'Valor inválido ou ausente.')
        # Regras de aprovação na criação/edição
        aprovado = cleaned.get('aprovado')
        data_aprovacao = cleaned.get('data_aprovacao')
        if not aprovado and data_aprovacao is not None:
            self.add_error('data_aprovacao', 'Informe data apenas quando aprovado = Sim.')
        
        return cleaned

class AnexosForm(forms.ModelForm):
    class Meta:
        model = Anexos
        fields = ['arquivo', 'nome_anexo', 'descricao']
        widgets = {
            'arquivo': forms.FileInput(attrs={'class': 'input w-full'}),
            'nome_anexo': forms.TextInput(attrs={'class': 'input w-full', 'placeholder': 'Nome do anexo'}),
            'descricao': forms.TextInput(attrs={'class': 'input w-full', 'placeholder': 'Descrição do conteúdo'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tornar os campos opcionais
        self.fields['nome_anexo'].required = False
        self.fields['descricao'].required = False
        self.fields['arquivo'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        arquivo = cleaned_data.get('arquivo')
        nome_anexo = cleaned_data.get('nome_anexo')
        descricao = cleaned_data.get('descricao')
        
        # Se não há arquivo mas há nome ou descrição, exigir o arquivo
        if not arquivo and not self.instance.pk and (nome_anexo or descricao):
            self.add_error('arquivo', 'É necessário incluir o arquivo para este anexo.')
            
        # Se não há arquivo nem dados, este form deve ser considerado vazio e não salvo
        if not arquivo and not nome_anexo and not descricao and not self.instance.pk:
            # Form vazio - não deve ser processado
            pass
            
        return cleaned_data

class BaseAnexosFormSet(BaseInlineFormSet):
    def clean(self):
        """
        Valida o formset e filtra formas vazias
        """
        super().clean()
        
        # Contar quantos anexos válidos temos
        valid_forms = 0
        incomplete_forms = 0
        
        # Validar cada formulário individualmente
        for i, form in enumerate(self.forms):
            # Ignorar forms marcados para delete
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                # Se tem arquivo, é um form válido
                if form.cleaned_data.get('arquivo'):
                    valid_forms += 1
                # Se não tem arquivo mas tem nome ou descrição, está incompleto
                elif form.cleaned_data.get('nome_anexo') or form.cleaned_data.get('descricao'):
                    incomplete_forms += 1
                    self.forms[i].add_error('arquivo', 'É necessário incluir o arquivo para este anexo.')
        
        # Se temos forms incompletos, mostrar erro ao nível do formset
        if incomplete_forms > 0:
            raise forms.ValidationError(
                f"Há {incomplete_forms} anexo(s) com nome ou descrição, mas sem arquivo. "
                "Por favor, selecione novamente os arquivos."
            )
            
        # Pelo menos um anexo é obrigatório? (Se desejar, pode remover esta validação)
        # if valid_forms == 0:
        #     raise forms.ValidationError('Pelo menos um anexo é obrigatório.')

# Cria um FormSet para gerenciar múltiplos anexos
AnexosFormSet = inlineformset_factory(
    Lancamentos, 
    Anexos, 
    form=AnexosForm, 
    formset=BaseAnexosFormSet,
    extra=1, 
    can_delete=True,
    can_delete_extra=True
)


class LancamentoApprovalForm(forms.ModelForm):
    aprovado = forms.TypedChoiceField(
        choices=[(True, 'Sim'), (False, 'Não')],
        coerce=lambda v: True if v in (True, 'True', 'true', '1', 1, 'on') else False,
        widget=forms.Select(attrs={'class': 'input w-full'})
    )
    data_aprovacao = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'input w-full'}),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S']
    )
    class Meta:
        model = Lancamentos
        fields = ['aprovado', 'data_aprovacao', 'observacao_aprovacao']
        widgets = {
            'observacao_aprovacao': forms.Textarea(attrs={'class': 'input w-full', 'rows': 3, 'placeholder': 'Observações sobre a aprovação (opcional)'}),
        }

    def clean(self):
        cleaned = super().clean()
        aprovado = cleaned.get('aprovado')
        data = cleaned.get('data_aprovacao')
        if aprovado and data is None:
            # opcionalmente permitir auto-preencher no save; não forçar aqui
            pass
        if not aprovado and data is not None:
            self.add_error('data_aprovacao', 'Informe data apenas quando aprovado = Sim.')
        return cleaned