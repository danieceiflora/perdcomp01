from django.shortcuts import render
from django.views.generic import CreateView
from .models import Contatos

class NewContatoView(CreateView):
    model = Contatos
    fields = '__all__'
    
    

