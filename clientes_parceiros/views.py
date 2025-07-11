from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from .models import ClientesParceiros, TipoRelacionamento
from .forms import ClientesParceirosForm, TipoRelacionamentoForm
class NewTipoRelacionamentoView(CreateView):
    model = TipoRelacionamento
    template_name = 'cadastrar_tipo_relacionamento.html'
    form_class = TipoRelacionamentoForm
    success_url = '/clientes-parceiros/tipo-relacionamento/'
    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipos_relacionamento'] = TipoRelacionamento.objects.all()
        return context
class TipoRelacionamentoListView(ListView):
    model = TipoRelacionamento
    template_name = 'cadastrar_tipo_relacionamento.html'
    context_object_name = 'tipos_relacionamento'

class TipoRelacionamentoUpdateView(UpdateView):
    model = TipoRelacionamento
    template_name = 'cadastrar_tipo_relacionamento.html'
    form_class = TipoRelacionamentoForm
    success_url = '/clientes-parceiros/tipo-relacionamento/'

class TipoRelacionamentoDeleteView(DeleteView):
    model = TipoRelacionamento
    template_name = 'excluir_tipo_relacionamento.html'
    success_url = reverse_lazy('lista_tipos_relacionamento')

class NewClienteParceiroView(CreateView):
    model = ClientesParceiros
    template_name = 'cadastrar_cliente_parceiro.html'
    form_class = ClientesParceirosForm
    success_url = reverse_lazy('lista_clientes_parceiros')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

class ListClienteParceiroView(ListView):
    model = ClientesParceiros
    template_name = 'lista_clientes_parceiros.html'
    context_object_name = 'clientes_parceiros'