from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Adesao
from .forms import AdesaoForm
from .permissions import AdesaoClientePermissionMixin

class AdesaoListView(AdesaoClientePermissionMixin, ListView):
    model = Adesao
    template_name = 'adesao/adesao_list.html'
    context_object_name = 'adesoes'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('cliente__id_company_vinculada', 'tese_credito_id')
        return queryset

class AdesaoCreateView(LoginRequiredMixin, CreateView):
    model = Adesao
    form_class = AdesaoForm
    template_name = 'adesao/adesao_form.html'
    success_url = reverse_lazy('adesao:list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Adesão cadastrada com sucesso!')
        return super().form_valid(form)

class AdesaoUpdateView(LoginRequiredMixin, UpdateView):
    model = Adesao
    form_class = AdesaoForm
    template_name = 'adesao/adesao_form.html'
    success_url = reverse_lazy('adesao:list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Adesão atualizada com sucesso!')
        return super().form_valid(form)

class AdesaoDeleteView(LoginRequiredMixin, DeleteView):
    model = Adesao
    template_name = 'adesao/adesao_confirm_delete.html'
    success_url = reverse_lazy('adesao:list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Adesão excluída com sucesso!')
        return super().delete(request, *args, **kwargs)
