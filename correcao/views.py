from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Correcao, tipoTese, TeseCredito
from .forms import CorrecaoForm, tipoTeseForm, TeseCreditoForm
from .permissions import AdminRequiredMixin

class CorrecaoListView(ListView):
    model = Correcao
    template_name = 'correcao/correcao_list.html'
    context_object_name = 'correcoes'
    paginate_by = 10

class CorrecaoCreateView(AdminRequiredMixin, CreateView):
    model = Correcao
    form_class = CorrecaoForm
    template_name = 'correcao/correcao_form.html'
    success_url = reverse_lazy('correcao:list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Correção cadastrada com sucesso!')
        return super().form_valid(form)

class CorrecaoUpdateView(AdminRequiredMixin, UpdateView):
    model = Correcao
    form_class = CorrecaoForm
    template_name = 'correcao/correcao_form.html'
    success_url = reverse_lazy('correcao:list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Correção atualizada com sucesso!')
        return super().form_valid(form)

class CorrecaoDeleteView(AdminRequiredMixin, DeleteView):
    model = Correcao
    template_name = 'correcao/correcao_confirm_delete.html'
    success_url = reverse_lazy('correcao:list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Correção excluída com sucesso!')
        return super().delete(request, *args, **kwargs)

# Views para tipoTese
class tipoTeseListView(ListView):
    model = tipoTese
    template_name = 'correcao/tipo_tese_list.html'
    context_object_name = 'tipos_tese'
    paginate_by = 10

class tipoTeseCreateView(AdminRequiredMixin, CreateView):
    model = tipoTese
    form_class = tipoTeseForm
    template_name = 'correcao/tipo_tese_form.html'
    success_url = reverse_lazy('correcao:tipo_tese_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Tipo de tese cadastrado com sucesso!')
        return super().form_valid(form)

class tipoTeseUpdateView(AdminRequiredMixin, UpdateView):
    model = tipoTese
    form_class = tipoTeseForm
    template_name = 'correcao/tipo_tese_form.html'
    success_url = reverse_lazy('correcao:tipo_tese_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Tipo de tese atualizado com sucesso!')
        return super().form_valid(form)

class tipoTeseDeleteView(AdminRequiredMixin, DeleteView):
    model = tipoTese
    template_name = 'correcao/tipo_tese_confirm_delete.html'
    success_url = reverse_lazy('correcao:tipo_tese_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Tipo de tese excluído com sucesso!')
        return super().delete(request, *args, **kwargs)

# Views para TeseCredito
class TeseCreditoListView(ListView):
    model = TeseCredito
    template_name = 'correcao/tese_credito_list.html'
    context_object_name = 'teses_credito'
    paginate_by = 10

class TeseCreditoCreateView(AdminRequiredMixin, CreateView):
    model = TeseCredito
    form_class = TeseCreditoForm
    template_name = 'correcao/tese_credito_form.html'
    success_url = reverse_lazy('correcao:tese_credito_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Tese de crédito cadastrada com sucesso!')
        return super().form_valid(form)

class TeseCreditoUpdateView(AdminRequiredMixin, UpdateView):
    model = TeseCredito
    form_class = TeseCreditoForm
    template_name = 'correcao/tese_credito_form.html'
    success_url = reverse_lazy('correcao:tese_credito_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Tese de crédito atualizada com sucesso!')
        return super().form_valid(form)

class TeseCreditoDeleteView(AdminRequiredMixin, DeleteView):
    model = TeseCredito
    template_name = 'correcao/tese_credito_confirm_delete.html'
    success_url = reverse_lazy('correcao:tese_credito_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Tese de crédito excluída com sucesso!')
        return super().delete(request, *args, **kwargs)
