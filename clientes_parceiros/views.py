
# === IMPORTS ===
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import CreateView, ListView, UpdateView
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json

from .models import ClientesParceiros, TipoRelacionamento
from .forms import NovoClienteForm, ContatoFormSet
from empresas.forms import EmpresaForm
from empresas.models import Empresa
from contatos.models import Contatos

# === FIM IMPORTS ===

# View para editar cliente usando o mesmo formulário e template do cadastro
class EditarClienteView(LoginRequiredMixin, UpdateView):
    model = ClientesParceiros
    form_class = NovoClienteForm
    template_name = 'clientes_parceiros/cadastrar_cliente.html'
    success_url = reverse_lazy('lista_clientes_parceiros')

    def get_object(self, queryset=None):
        return get_object_or_404(ClientesParceiros, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente_parceiro = self.object
        # Empresa vinculada (cliente)
        if self.request.POST:
            context['empresa_form'] = EmpresaForm(self.request.POST, self.request.FILES, instance=cliente_parceiro.id_company_vinculada, prefix='empresa')
            contatos_qs = cliente_parceiro.id_company_vinculada.empresa_base_contato.all()
            context['contato_formset'] = ContatoFormSet(self.request.POST, initial=[{'tipo_contato': c.tipo_contato, 'telefone': c.telefone, 'email': c.email, 'site': c.site} for c in contatos_qs])
        else:
            context['empresa_form'] = EmpresaForm(instance=cliente_parceiro.id_company_vinculada, prefix='empresa')
            contatos_qs = cliente_parceiro.id_company_vinculada.empresa_base_contato.all()
            initial = [{'tipo_contato': c.tipo_contato, 'telefone': c.telefone, 'email': c.email, 'site': c.site} for c in contatos_qs]
            context['contato_formset'] = ContatoFormSet(initial=initial)
        # Empresa base: apenas a vinculada ao usuário logado
        empresa_vinculada = None
        if hasattr(self.request.user, 'profile'):
            empresa_vinculada = self.request.user.profile.empresa_vinculada
        context['parceiros'] = Empresa.objects.filter(id=empresa_vinculada.id) if empresa_vinculada else Empresa.objects.none()
        # Vínculo: apenas 'cliente'
        context['vinculos'] = TipoRelacionamento.objects.filter(tipo_relacionamento__iexact='cliente')
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        # Filtra o campo parceiro e vinculo no formulário
        empresa_vinculada = None
        if hasattr(self.request.user, 'profile'):
            empresa_vinculada = self.request.user.profile.empresa_vinculada
            if empresa_vinculada:
                self.form_class.base_fields['parceiro'].queryset = Empresa.objects.filter(id=empresa_vinculada.id)
        self.form_class.base_fields['vinculo'].queryset = TipoRelacionamento.objects.filter(tipo_relacionamento__iexact='cliente')
        return kwargs

    def form_valid(self, form):
        context = self.get_context_data()
        empresa_form = context['empresa_form']
        contato_formset = context['contato_formset']
        cliente_parceiro = self.object
        if form.is_valid() and empresa_form.is_valid() and contato_formset.is_valid():
            with transaction.atomic():
                try:
                    # Atualiza empresa vinculada
                    empresa = empresa_form.save()
                    # Atualiza vínculo
                    cliente_parceiro.id_company_base = form.cleaned_data['parceiro']
                    cliente_parceiro.id_company_vinculada = empresa
                    cliente_parceiro.id_tipo_relacionamento = form.cleaned_data['vinculo']
                    cliente_parceiro.nome_referencia = form.cleaned_data['nome_referencia']
                    cliente_parceiro.cargo_referencia = form.cleaned_data['cargo_referencia']
                    cliente_parceiro.save()
                    # Atualiza contatos: remove todos e recria
                    empresa.empresa_base_contato.all().delete()
                    for contato_form in contato_formset:
                        if contato_form.cleaned_data and not contato_form.cleaned_data.get('DELETE', False):
                            contato = contato_form.save(commit=False)
                            contato.empresa_base = empresa
                            contato.save()
                    messages.success(self.request, f'Cliente "{empresa}" atualizado com sucesso!')
                    return redirect(self.success_url)
                except Exception as e:
                    messages.error(self.request, f'Erro ao atualizar cliente: {str(e)}')
                    return self.form_invalid(form)
        else:
            if not empresa_form.is_valid():
                messages.error(self.request, 'Há erros no cadastro da empresa.')
            if not contato_formset.is_valid():
                messages.error(self.request, 'Há erros nos dados de contato. Verifique os campos.')
            return self.form_invalid(form)

class NovoClienteView(LoginRequiredMixin, CreateView):
    """
    View para cadastrar novo cliente com parceiro, dados de contato e vínculo
    """
    model = ClientesParceiros
    form_class = NovoClienteForm
    template_name = 'clientes_parceiros/cadastrar_cliente.html'
    success_url = reverse_lazy('lista_clientes_parceiros')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obter empresa vinculada ao usuário logado
        empresa_vinculada = None
        if hasattr(self.request.user, 'profile'):
            empresa_vinculada = self.request.user.profile.empresa_vinculada
        # Formulário de nova empresa
        if self.request.POST:
            context['empresa_form'] = EmpresaForm(self.request.POST, self.request.FILES, prefix='empresa')
            context['contato_formset'] = ContatoFormSet(self.request.POST)
        else:
            context['empresa_form'] = EmpresaForm(prefix='empresa')
            context['contato_formset'] = ContatoFormSet()
        # Só mostra a empresa vinculada ao usuário
        context['parceiros'] = Empresa.objects.filter(id=empresa_vinculada.id) if empresa_vinculada else Empresa.objects.none()
        # Só mostra o vínculo 'cliente'
        context['vinculos'] = TipoRelacionamento.objects.filter(tipo_relacionamento__iexact='cliente')
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        # Filtra o campo parceiro e vinculo no formulário
        if hasattr(self.request.user, 'profile'):
            empresa_vinculada = self.request.user.profile.empresa_vinculada
            if empresa_vinculada:
                self.form_class.base_fields['parceiro'].queryset = Empresa.objects.filter(id=empresa_vinculada.id)
        self.form_class.base_fields['vinculo'].queryset = TipoRelacionamento.objects.filter(tipo_relacionamento__iexact='cliente')
        return kwargs
    
    def form_valid(self, form):
        context = self.get_context_data()
        empresa_form = context['empresa_form']
        contato_formset = context['contato_formset']
        
        # Validar todos os formulários
        if form.is_valid() and empresa_form.is_valid() and contato_formset.is_valid():
            with transaction.atomic():
                try:
                    # Salvar nova empresa
                    nova_empresa = empresa_form.save()
                    # Pegar os dados do formulário principal
                    parceiro = form.cleaned_data['parceiro']
                    cliente = nova_empresa
                    vinculo = form.cleaned_data['vinculo']
                    # Criar o relacionamento cliente-parceiro
                    cliente_parceiro = ClientesParceiros(
                        id_company_base=parceiro,
                        id_company_vinculada=cliente,
                        id_tipo_relacionamento=vinculo,
                        nome_referencia=form.cleaned_data['nome_referencia'],
                        cargo_referencia=form.cleaned_data['cargo_referencia']
                    )
                    cliente_parceiro.save()
                    # Salvar os contatos associados ao cliente
                    for contato_form in contato_formset:
                        if contato_form.cleaned_data and not contato_form.cleaned_data.get('DELETE', False):
                            contato = contato_form.save(commit=False)
                            contato.empresa_base = cliente  # Associa ao cliente
                            contato.save()
                    messages.success(
                        self.request, 
                        f'Cliente "{cliente}" cadastrado com sucesso como "{vinculo}" do parceiro "{parceiro}"!'
                    )
                    return redirect(self.success_url)
                except Exception as e:
                    messages.error(
                        self.request, 
                        f'Erro ao cadastrar cliente: {str(e)}'
                    )
                    return self.form_invalid(form)
        else:
            if not empresa_form.is_valid():
                messages.error(self.request, 'Há erros no cadastro da nova empresa.')
            if not contato_formset.is_valid():
                messages.error(self.request, 'Há erros nos dados de contato. Verifique os campos.')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request, 
            'Há erros no formulário. Verifique os dados e tente novamente.'
        )
        return super().form_invalid(form)

class ListClienteParceiroView(LoginRequiredMixin, ListView):
    """
    View para listar clientes e parceiros cadastrados
    """
    model = ClientesParceiros
    template_name = 'clientes_parceiros/lista_clientes.html'
    context_object_name = 'clientes_parceiros'
    paginate_by = 20
    
    def get_queryset(self):
        qs = ClientesParceiros.objects.select_related(
            'id_company_base', 
            'id_company_vinculada', 
            'id_tipo_relacionamento'
        ).filter(ativo=True)
        # Filtra apenas os clientes do parceiro logado
        empresa_vinculada = None
        if hasattr(self.request.user, 'profile'):
            empresa_vinculada = self.request.user.profile.empresa_vinculada
        if empresa_vinculada:
            qs = qs.filter(id_company_base=empresa_vinculada)
        return qs.order_by('-data_inicio_parceria')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        clientes_parceiros = context['clientes_parceiros']
        context['total_relacionamentos'] = clientes_parceiros.count()
        context['total_clientes_unicos'] = len(set(cp.id_company_vinculada_id for cp in clientes_parceiros))
        context['total_parceiros_unicos'] = len(set(cp.id_company_base_id for cp in clientes_parceiros))
        context['total_vinculos_unicos'] = len(set(cp.id_tipo_relacionamento_id for cp in clientes_parceiros))
        return context

class ClienteParceiroUpdateView(LoginRequiredMixin, UpdateView):
    """
    View para editar relacionamento cliente-parceiro
    """
    model = ClientesParceiros
    form_class = NovoClienteForm
    template_name = 'clientes_parceiros/editar_cliente.html'
    success_url = reverse_lazy('lista_clientes_parceiros')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_initial(self):
        initial = super().get_initial()
        if self.object:
            initial['parceiro'] = self.object.id_company_base
            initial['cliente'] = self.object.id_company_vinculada
            initial['vinculo'] = self.object.id_tipo_relacionamento
        return initial

# Views para AJAX (se necessário)
@method_decorator(csrf_exempt, name='dispatch')
class EmpresasAjaxView(LoginRequiredMixin, View):
    """
    View para buscar empresas via AJAX
    """
    def get(self, request, *args, **kwargs):
        term = request.GET.get('term', '')
        empresas = Empresa.objects.filter(
            razao_social__icontains=term
        )[:10]
        
        results = []
        for empresa in empresas:
            results.append({
                'id': empresa.id,
                'text': empresa.razao_social,
                'fantasia': empresa.nome_fantasia
            })
        
        return JsonResponse({'results': results})

# Views para Tipo de Relacionamento
class NewTipoRelacionamentoView(LoginRequiredMixin, CreateView):
    model = TipoRelacionamento
    fields = ['tipo_relacionamento']
    template_name = 'clientes_parceiros/cadastrar_tipo_relacionamento.html'
    success_url = reverse_lazy('lista_tipos_relacionamento')

class TipoRelacionamentoListView(LoginRequiredMixin, ListView):
    model = TipoRelacionamento
    template_name = 'clientes_parceiros/lista_tipos_relacionamento.html'
    context_object_name = 'tipos_relacionamento'

class TipoRelacionamentoUpdateView(LoginRequiredMixin, UpdateView):
    model = TipoRelacionamento
    fields = ['tipo_relacionamento']
    template_name = 'clientes_parceiros/editar_tipo_relacionamento.html'
    success_url = reverse_lazy('lista_tipos_relacionamento')

# Mantendo compatibilidade com URLs existentes
NewClienteParceiroView = NovoClienteView
