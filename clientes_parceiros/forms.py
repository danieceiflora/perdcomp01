from django import forms
from clientes_parceiros.models import ClientesParceiros, TipoRelacionamento

class TipoRelacionamentoForm(forms.ModelForm):
    class Meta:
        model = TipoRelacionamento
        fields = ['tipo_relacionamento']

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
    