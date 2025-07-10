from django import forms
from .models import Contatos

class ContatoForm(forms.ModelForm):
    class Meta:
        model = Contatos
        fields = '__all__'

