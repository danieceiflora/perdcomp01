from django import forms
from empresas.models import Empresa


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = '__all__'
        widgets = {
          'logomarca': forms.FileInput(attrs={'accept': 'image/*'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
              field.widget.attrs['class'] = 'form-control'
         