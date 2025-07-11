from django import forms
from clientes_parceiros.models import ClientesParceiros, TipoRelacionamento
from empresas.models import Empresa
from contatos.models import Contatos

class TipoRelacionamentoForm(forms.ModelForm):
    class Meta:
        model = TipoRelacionamento
        fields = ['tipo_relacionamento']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
                field.widget.attrs['class'] = 'form-control'

class EmpresaClienteParceiroForm(forms.ModelForm):
    # Campo para selecionar a empresa base (já existente)
    empresa_base = forms.ModelChoiceField(
        queryset=Empresa.objects.all(),
        label='Empresa Base',
        required=True,
        empty_label="Selecione a empresa base"
    )
    
    # Campos para nova empresa vinculada
    cnpj = forms.CharField(max_length=20, label='CNPJ da Nova Empresa', required=True)
    razao_social = forms.CharField(max_length=100, label='Razão Social da Nova Empresa', required=True)
    nome_fantasia = forms.CharField(max_length=100, label='Nome Fantasia da Nova Empresa', required=False)
    codigo_origem = forms.CharField(max_length=20, label='Código de Origem da Nova Empresa', required=False)
    logomarca = forms.ImageField(label='Logomarca da Nova Empresa', required=False)
    
    # Outros campos
    data_inicio_parceria = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        label='Data de Início da Parceria'
    )
    
    class Meta:
        model = ClientesParceiros
        fields = ['id_tipo_relacionamento', 'nome_referencia', 'cargo_referencia', 'data_inicio_parceria']
        
    def clean(self):
        cleaned_data = super().clean()
        empresa_base = cleaned_data.get('empresa_base')
        cnpj = cleaned_data.get('cnpj')
        razao_social = cleaned_data.get('razao_social')
        
        # Empresa base é obrigatória
        if not empresa_base:
            self.add_error('empresa_base', 'É necessário selecionar uma empresa base.')
            
        # Validar campos da nova empresa vinculada
        if not cnpj:
            self.add_error('cnpj', 'CNPJ da nova empresa é obrigatório.')
        if not razao_social:
            self.add_error('razao_social', 'Razão Social da nova empresa é obrigatória.')
        
        return cleaned_data
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class ClientesParceirosForm(forms.ModelForm):
    class Meta:
        model = ClientesParceiros
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
                field.widget.attrs['class'] = 'form-control'
    