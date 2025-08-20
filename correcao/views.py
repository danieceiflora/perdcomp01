from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count
from django.db.models import ProtectedError
from .models import Correcao, tipoTese, TeseCredito
from .forms import CorrecaoForm, tipoTeseForm, TeseCreditoForm
from .permissions import AdminRequiredMixin

class CorrecaoListView(ListView):
    model = Correcao
    template_name = 'correcao/correcao_list.html'
    context_object_name = 'correcoes'
    paginate_by = 10
    def get_queryset(self):
        # Anotar quantidade de teses para evitar N+1 no template
        return Correcao.objects.all().annotate(teses_total=Count('tesecredito'))

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
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = self.object
        referencias = obj.tesecredito_set.all()
        ctx['has_references'] = referencias.exists()
        ctx['referencias'] = referencias
        return ctx

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, 'Correção excluída com sucesso!')
            return response
        except ProtectedError:
            messages.error(self.request, 'Não é possível excluir: há teses vinculadas a esta correção.')
            return redirect(self.success_url)

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
    
    def get_queryset(self):
        # Anotar quantidade de adesões para cada tese
        return TeseCredito.objects.all().annotate(adesoes_total=Count('adesoes'))

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
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = self.object
        referencias = obj.adesoes.all()
        ctx['has_references'] = referencias.exists()
        ctx['referencias'] = referencias
        return ctx
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, 'Tese de crédito excluída com sucesso!')
            return response
        except ProtectedError:
            messages.error(self.request, 'Não é possível excluir: há adesões vinculadas a esta tese de crédito.')
            return redirect(self.success_url)
