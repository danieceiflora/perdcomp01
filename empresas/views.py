from django.shortcuts import render
from empresas.forms import EmpresaForm
from empresas.models import Empresa
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from django.contrib import messages
import os
from django.conf import settings
import uuid


def home_view(request):
  return render(request, 'base.html')

class NewEmpresaView(CreateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = 'cadastro_empresa.html'
    success_url = '/empresas/lista-empresas/'

    def form_valid(self, form):
        logomarca_file = self.request.FILES.get('logomarca')
        empresa = form.save(commit=False)
       
        empresa.save()
        messages.success(self.request, 'Empresa cadastrada com sucesso!')
        return super().form_valid(form)


class EmpresaListView(ListView):
    model = Empresa
    template_name = 'empresas_list.html'
    context_object_name = 'empresas'

class EmpresaUpdateView(UpdateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = 'editar_empresa.html'
    success_url = '/empresas/lista-empresas/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = EmpresaForm(instance=self.object)
        return context