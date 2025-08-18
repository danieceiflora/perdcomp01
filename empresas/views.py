from django.shortcuts import render
from empresas.forms import EmpresaForm
from empresas.models import Empresa
from contatos.models import Contatos
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
import os
from django.conf import settings
import uuid


def home_view(request):
  return render(request, 'base.html')
class NewEmpresaView(CreateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = 'cadastro_empresa.html'
    success_url = reverse_lazy('empresas:lista_empresas')

    def form_valid(self, form):
        # Save the empresa instance first
        empresa = form.save()
        
        # Get the number of contacts from the form
        contact_count = int(self.request.POST.get('contact_count', 0))
        
        # Process each contact form
        for i in range(1, contact_count + 1):
            tipo_contato = self.request.POST.get(f'tipo_contato_{i}')
            telefone = self.request.POST.get(f'telefone_{i}')
            email = self.request.POST.get(f'email_{i}')
            site = self.request.POST.get(f'site_{i}')
            
            # Create a new contact record if data is provided
            if telefone or email or site:
                Contatos.objects.create(
                    tipo_contato=tipo_contato,
                    empresa_base=empresa,
                    telefone=telefone or "",
                    email=email or "",
                    site=site or ""
                )
        
        messages.success(self.request, 'Empresa cadastrada com sucesso!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipo_contato_options'] = Contatos.tipo_contato_options
        return context

class EmpresaListView(ListView):
    model = Empresa
    template_name = 'empresas_list.html'
    context_object_name = 'empresas'
    
class EmpresaUpdateView(UpdateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = 'editar_empresa.html'
    success_url = reverse_lazy('empresas:lista_empresas')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all contacts for this company
        contatos = Contatos.objects.filter(empresa_base=self.object)
        
        context['form'] = EmpresaForm(instance=self.object)
        context['tipo_contato_options'] = Contatos.tipo_contato_options
        context['contatos'] = contatos
        
        return context
    
    def form_valid(self, form):
        empresa = form.save()
        
        # Get the number of contacts from the form
        contact_count = int(self.request.POST.get('contact_count', 0))
        
        # Process each contact form
        for i in range(1, contact_count + 1):
            tipo_contato = self.request.POST.get(f'tipo_contato_{i}')
            telefone = self.request.POST.get(f'telefone_{i}')
            email = self.request.POST.get(f'email_{i}')
            site = self.request.POST.get(f'site_{i}')
            contato_id = self.request.POST.get(f'contato_id_{i}')
            
            # If contact data is provided
            if telefone or email or site:
                if contato_id:
                    # Update existing contact
                    try:
                        contato = Contatos.objects.get(id=contato_id)
                        contato.tipo_contato = tipo_contato
                        contato.telefone = telefone or ""
                        contato.email = email or ""
                        contato.site = site or ""
                        contato.save()
                    except Contatos.DoesNotExist:
                        # If the contact doesn't exist anymore, create a new one
                        Contatos.objects.create(
                            tipo_contato=tipo_contato,
                            empresa_base=empresa,
                            telefone=telefone or "",
                            email=email or "",
                            site=site or ""
                        )
                else:
                    # Create new contact
                    Contatos.objects.create(
                        tipo_contato=tipo_contato,
                        empresa_base=empresa,
                        telefone=telefone or "",
                        email=email or "",
                        site=site or ""
                    )
        
        messages.success(self.request, 'Empresa atualizada com sucesso!')
        return super().form_valid(form)

class EmpresaDeleteView(DeleteView):
    model = Empresa
    template_name = 'excluir_empresa.html'
    success_url = reverse_lazy('empresas:lista_empresas')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Empresa excluída com sucesso!')
        return super().delete(request, *args, **kwargs)