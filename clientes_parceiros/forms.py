from django import forms
from django.forms import formset_factory
from .models import ClientesParceiros, TipoRelacionamento
from empresas.models import Empresa
from contatos.models import Contatos

class NovoClienteForm(forms.ModelForm):
    """
    Formulário para cadastrar novo cliente com seções:
    1. Seleção do Parceiro (empresa_base)
    2. Dados do Cliente (empresa_vinculada) 
    3. Seleção do Vínculo
    """
    
    # Seção 1: Seleção do Parceiro
    parceiro = forms.ModelChoiceField(
        queryset=Empresa.objects.all(),
        empty_label="Selecione o parceiro...",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_parceiro'
        }),
        label="Parceiro",
        help_text="Selecione a empresa parceira"
    )
    

    
    nome_referencia = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nome da pessoa de referência'
        }),
        label="Nome de Referência",
        help_text="Nome da pessoa responsável pelo relacionamento"
    )
    
    cargo_referencia = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cargo da pessoa de referência'
        }),
        label="Cargo de Referência",
        help_text="Cargo da pessoa responsável (opcional)"
    )
    
    # Seção 3: Seleção do Vínculo
    vinculo = forms.ModelChoiceField(
        queryset=TipoRelacionamento.objects.all(),
        empty_label="Selecione o tipo de vínculo...",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_vinculo'
        }),
        label="Tipo de Vínculo",
        help_text="Selecione o tipo de relacionamento entre as empresas"
    )

    class Meta:
        model = ClientesParceiros
        fields = ['nome_referencia', 'cargo_referencia']
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Se o usuário estiver logado, podemos filtrar as empresas
        if self.user:
            # Aqui você pode adicionar lógica para filtrar empresas baseado no usuário
            pass
            
    def clean(self):
        cleaned_data = super().clean()
        # A validação de cliente agora é feita na view, pois a empresa será criada pelo EmpresaForm
        return cleaned_data

class ContatoForm(forms.ModelForm):
    """
    Formulário para dados de contato do cliente
    """
    class Meta:
        model = Contatos
        fields = ['tipo_contato', 'telefone', 'email', 'site']
        widgets = {
            'tipo_contato': forms.Select(attrs={
                'class': 'form-control'
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(11) 99999-9999'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'exemplo@email.com'
            }),
            'site': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.exemplo.com.br'
            })
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Torna o campo site opcional
        self.fields['site'].required = False

# Criando um formset para múltiplos contatos
ContatoFormSet = formset_factory(
    ContatoForm, 
    extra=1,  # Começa com 1 formulário vazio
    can_delete=True,
    min_num=1,  # Pelo menos 1 contato obrigatório
    validate_min=True
)
