from django import forms
from empresas.models import Empresa
from utils.validators import validate_cnpj

class EmpresaForm(forms.ModelForm):
    cnpj = forms.CharField(
        label="CNPJ",
        validators=[validate_cnpj],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'maxlength': '18',  # Define o tamanho máximo aqui
            'data-mask': 'cnpj' # Atributo para o seletor JS
        })
    )
    class Meta:
        model = Empresa
        fields = '__all__'
        widgets = {
          'logomarca': forms.FileInput(attrs={'accept': 'image/*'}),
        }
    def clean_cnpj(self):
        cnpj = self.cleaned_data.get('cnpj')
        if cnpj:
            # Remove todos os caracteres que não são números ou letras
            return ''.join(filter(str.isalnum, cnpj))
        return cnpj

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove a classe 'form-control' do campo de logomarca para estilização customizada se necessário
        if 'logomarca' in self.fields:
            self.fields['logomarca'].widget.attrs.pop('class', None)

        # Adiciona a classe 'form-control' aos outros campos
        for field_name, field in self.fields.items():
            if field_name != 'logomarca' and field_name != 'cnpj':
                field.widget.attrs['class'] = 'form-control'