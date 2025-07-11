from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Correcao
from .forms import CorrecaoForm

class CorrecaoListView(ListView):
    model = Correcao
    template_name = 'correcao/correcao_list.html'
    context_object_name = 'correcoes'
    paginate_by = 10

class CorrecaoCreateView(CreateView):
    model = Correcao
    form_class = CorrecaoForm
    template_name = 'correcao/correcao_form.html'
    success_url = reverse_lazy('correcao:list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Correção cadastrada com sucesso!')
        return super().form_valid(form)

class CorrecaoUpdateView(UpdateView):
    model = Correcao
    form_class = CorrecaoForm
    template_name = 'correcao/correcao_form.html'
    success_url = reverse_lazy('correcao:list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Correção atualizada com sucesso!')
        return super().form_valid(form)

class CorrecaoDeleteView(DeleteView):
    model = Correcao
    template_name = 'correcao/correcao_confirm_delete.html'
    success_url = reverse_lazy('correcao:list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Correção excluída com sucesso!')
        return super().delete(request, *args, **kwargs)
