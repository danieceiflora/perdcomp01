# AJAX para empresas disponíveis conforme tipo de relacionamento
from django.views.decorators.http import require_GET

# === IMPORTS ===
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import CreateView, ListView, UpdateView
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, Http404
from django.utils.decorators import method_decorator
from django.views import View
import json
from django.contrib.auth.mixins import UserPassesTestMixin
from django import forms
from django.db import models
from django.db.models import Q
from django.utils.timezone import localtime
from django.utils.dateformat import format as date_format
from django.contrib.auth.decorators import login_required

from .models import ClientesParceiros
from .forms import NovoClienteForm, ContatoFormSet, NovoParceiroForm
from empresas.forms import EmpresaForm
from empresas.models import Empresa
from contatos.models import Contatos
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import ClientesParceirosSerializer

# === FIM IMPORTS ===

@require_GET
def empresas_disponiveis_ajax(request, tipo_id):
    # Busca empresas já vinculadas como id_company_vinculada para o tipo selecionado
    empresas_vinculadas = ClientesParceiros.objects.filter(tipo_parceria=tipo_id).values_list('id_company_vinculada', flat=True)
    empresas = Empresa.objects.exclude(pk__in=empresas_vinculadas)
    data = [{'id': e.pk, 'nome': str(e)} for e in empresas]
    return JsonResponse({'empresas': data})


# View para editar cliente usando o mesmo formulário e template do cadastro
class EditarClienteView(LoginRequiredMixin, UpdateView):
    model = ClientesParceiros
    form_class = NovoClienteForm
    template_name = 'cadastrar_cliente.html'
    success_url = reverse_lazy('lista_clientes')

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
            initial = [{'tipo_contato': c.tipo_contato, 'telefone': c.telefone, 'email': c.email, 'site': c.site} for c in contatos_qs] or [{}]
            context['contato_formset'] = ContatoFormSet(initial=initial)
        # Empresa base: apenas a vinculada ao usuário logado
        empresa_vinculada = None
        if hasattr(self.request.user, 'profile'):
            empresa_vinculada = self.request.user.profile.empresa_vinculada
        context['parceiros'] = Empresa.objects.filter(id=empresa_vinculada.id) if empresa_vinculada else Empresa.objects.none()
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Campo 'parceiro' deve listar somente empresas cadastradas como parceiros
        partner_ids = ClientesParceiros.objects.filter(tipo_parceria='parceiro').values_list('id_company_vinculada_id', flat=True).distinct()
        if 'parceiro' in form.fields:
            # Ao editar, bloqueia o campo parceiro e mantém o parceiro atual
            current_partner = self.object.id_company_base
            field = form.fields['parceiro']
            field.queryset = Empresa.objects.filter(id=current_partner.id)
            # Remove o empty_label para não mostrar "Selecione o parceiro"
            if hasattr(field, 'empty_label'):
                field.empty_label = None
            # Garante que o initial esteja definido
            form.initial['parceiro'] = current_partner.pk
            form.fields['parceiro'].disabled = True
            # Ajusta atributos do widget
            css = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f"{css} disabled".strip()
            field.widget.attrs['readonly'] = 'readonly'
            field.help_text = 'Não é possível alterar o parceiro vinculado após a criação do cliente'
        return form

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
                    # Atualiza vínculo - mantém parceiro original
                    # Não usa form.cleaned_data['parceiro'] porque o campo está disabled
                    # cliente_parceiro.id_company_base não muda - mantém o parceiro original
                    cliente_parceiro.id_company_vinculada = empresa
                    cliente_parceiro.tipo_parceria = 'cliente'
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

class NovoClienteView(UserPassesTestMixin, LoginRequiredMixin, CreateView):
    """
    View para cadastrar novo cliente com parceiro, dados de contato e vínculo
    """

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff
        
    model = ClientesParceiros
    form_class = NovoClienteForm
    template_name = 'cadastrar_cliente.html'
    success_url = reverse_lazy('lista_clientes')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obter empresa vinculada ao usuário logado
        empresa_vinculada = None
        if hasattr(self.request.user, 'profile'):
            empresa_vinculada = self.request.user.profile.empresa_vinculada
        # Formulário de nova empresa
        if self.request.POST:
            context['empresa_form'] = EmpresaForm(self.request.POST, self.request.FILES, prefix='empresa')
            context['contato_formset'] = ContatoFormSet(self.request.POST, initial=[{}])
        else:
            context['empresa_form'] = EmpresaForm(prefix='empresa')
            context['contato_formset'] = ContatoFormSet(initial=[{}])
        # Só mostra a empresa vinculada ao usuário
        context['parceiros'] = Empresa.objects.filter(id=empresa_vinculada.id) if empresa_vinculada else Empresa.objects.none()
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Campo 'parceiro' lista apenas empresas que já são parceiros
        partner_ids = ClientesParceiros.objects.filter(tipo_parceria='parceiro').values_list('id_company_vinculada_id', flat=True).distinct()
        if 'parceiro' in form.fields:
            form.fields['parceiro'].queryset = Empresa.objects.filter(id__in=partner_ids).order_by('razao_social')
        return form
    
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
                    # tipo_parceria fixo = 'cliente'
                    cliente_parceiro = ClientesParceiros(
                        id_company_base=parceiro,
                        id_company_vinculada=cliente,
                        tipo_parceria='cliente',
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
                        f'Cliente "{cliente}" cadastrado com sucesso para o parceiro "{parceiro}"!'
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
    View para listar somente clientes cadastrados (tipo_parceria='cliente')
    """
    model = ClientesParceiros
    template_name = 'lista_clientes.html'
    context_object_name = 'clientes_parceiros'
    paginate_by = 20
    
    def get_queryset(self):
        qs = ClientesParceiros.objects.select_related(
            'id_company_base', 
            'id_company_vinculada'
        ).filter(ativo=True, tipo_parceria='cliente')  # agora só clientes
        # Filtro por parceiro específico via GET (parceiro=<id>)
        parceiro_id = self.request.GET.get('parceiro')
        empresa_vinculada = getattr(getattr(self.request.user, 'profile', None), 'empresa_vinculada', None)
        # Se usuário comum (não staff/superuser), restringe sempre à empresa vinculada
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            if empresa_vinculada:
                qs = qs.filter(id_company_base=empresa_vinculada)
        else:
            # Admin pode filtrar por qualquer parceiro
            if parceiro_id:
                qs = qs.filter(id_company_base_id=parceiro_id)
            elif empresa_vinculada:
                # Se quiser que admin veja todos por padrão, não aplicar este filtro.
                # Deixe comentado para mostrar todos.
                pass
        # Filtro de busca
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(id_company_vinculada__razao_social__icontains=q) |
                Q(id_company_vinculada__nome_fantasia__icontains=q) |
                Q(id_company_vinculada__cnpj__icontains=q)
            )
        return qs.order_by('-data_inicio_parceria')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        clientes_parceiros = context['clientes_parceiros']
        context['total_clientes'] = clientes_parceiros.count()
        context['total_empresas_cliente_unicas'] = len(set(cp.id_company_vinculada_id for cp in clientes_parceiros))
        context['empresa_base_atual'] = getattr(getattr(self.request.user, 'profile', None), 'empresa_vinculada', None)
        context['q'] = self.request.GET.get('q', '')
        
        # Calcular total de parceiros
        parceiros_qs = ClientesParceiros.objects.filter(tipo_parceria='parceiro', ativo=True)
        context['total_parceiros'] = parceiros_qs.count()
        
        # Lista de parceiros para filtro (apenas para staff/superuser)
        if self.request.user.is_staff or self.request.user.is_superuser:
            # Parceiros são empresas que aparecem como base em vínculos de cliente
            partner_ids = ClientesParceiros.objects.filter(tipo_parceria='cliente').values_list('id_company_base_id', flat=True).distinct()
            context['parceiros_filtro'] = Empresa.objects.filter(id__in=partner_ids).order_by('razao_social')
            context['parceiro_selecionado'] = self.request.GET.get('parceiro', '')
        return context

class ListParceirosView(LoginRequiredMixin, ListView):
    """Lista somente vínculos cujo tipo_parceria = 'parceiro'."""
    model = ClientesParceiros
    template_name = 'lista_parceiros.html'
    context_object_name = 'parceiros'
    paginate_by = 20

    def get_queryset(self):
        qs = ClientesParceiros.objects.select_related('id_company_base', 'id_company_vinculada').filter(
            ativo=True,
            tipo_parceria='parceiro'
        )
        empresa_vinculada = getattr(getattr(self.request.user, 'profile', None), 'empresa_vinculada', None)
        if empresa_vinculada:
            qs = qs.filter(id_company_base=empresa_vinculada)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(id_company_vinculada__razao_social__icontains=q) |
                Q(id_company_vinculada__nome_fantasia__icontains=q) |
                Q(id_company_vinculada__cnpj__icontains=q)
            )
        return qs.order_by('-data_inicio_parceria')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parceiros = context['parceiros']
        context['total_parceiros'] = parceiros.count()
        context['total_empresas_unicas'] = len(set(p.id_company_vinculada_id for p in parceiros))
        context['q'] = self.request.GET.get('q', '')
        return context


# ============ HISTÓRICO (JSON) ============
@login_required
@require_GET
def clientes_parceiros_history_json(request, pk):
    """Retorna histórico JSON (cliente ou parceiro) com diffs campo a campo."""
    try:
        obj = ClientesParceiros.objects.get(pk=pk)
    except ClientesParceiros.DoesNotExist:
        raise Http404
    manager = getattr(obj, 'history', None) or getattr(obj, 'historico', None)
    if manager is None:
        return JsonResponse({'error': 'Histórico não configurado.'}, status=400)
    history = list(manager.all().order_by('history_date'))
    result = []
    def serialize_value(val):
        from django.db.models import Model
        import datetime
        if val is None:
            return None
        if isinstance(val, Model):
            # Prefer nome_fantasia/razao_social when Empresa
            if hasattr(val, 'nome_fantasia') or hasattr(val, 'razao_social'):
                try:
                    return getattr(val, 'nome_fantasia') or getattr(val, 'razao_social') or str(val.pk)
                except Exception:
                    return str(val)
            return str(val)
        if isinstance(val, (datetime.datetime, datetime.date, datetime.time)):
            try:
                return val.isoformat()
            except Exception:
                return str(val)
        if isinstance(val, (list, tuple, set)):
            return [serialize_value(v) for v in val]
        return val

    for idx, record in enumerate(history):
        entry = {
            'id': record.id,
            'history_id': getattr(record, 'history_id', None),
            'history_date': date_format(localtime(record.history_date), 'd/m/Y H:i:s'),
            'history_user': getattr(record.history_user, 'username', None),
            'history_type': record.history_type,
            'changes': [],
            'note': ''
        }
        if idx == 0:
            # registro inicial -> listar valores
            if entry['history_type'] not in ('+','~','-'):
                entry['history_type'] = '+'
            for field in record._meta.fields:
                fname = field.name
                if fname in ('history_id','history_date','history_change_reason','history_type','history_user','id'):
                    continue
                try:
                    val = getattr(record, fname)
                except Exception:
                    val = None
                if val not in (None, ''):
                    entry['changes'].append({'field': fname, 'old': None, 'new': serialize_value(val)})
        else:
            prev = history[idx-1]
            try:
                diff = record.diff_against(prev)
                for c in diff.changes:
                    entry['changes'].append({'field': c.field, 'old': serialize_value(c.old), 'new': serialize_value(c.new)})
            except Exception:
                pass
            # Fallback manual diff if diff_against returned nothing
            if not entry['changes']:
                ignore = {'history_id','history_date','history_change_reason','history_type','history_user','id'}
                manual_changes = []
                for field in record._meta.fields:
                    fname = field.name
                    if fname in ignore:
                        continue
                    try:
                        curr_val = getattr(record, fname)
                        prev_val = getattr(prev, fname)
                    except Exception:
                        continue
                    if curr_val != prev_val:
                        manual_changes.append({
                            'field': fname,
                            'old': serialize_value(prev_val),
                            'new': serialize_value(curr_val)
                        })
                if manual_changes:
                    entry['changes'] = manual_changes
                else:
                    entry['note'] = 'Alteração sem mudança nos campos deste vínculo (possível alteração em dados da empresa relacionada).'
        result.append(entry)
    result.reverse()
    return JsonResponse({'object_id': obj.id, 'history': result})

class ClienteParceiroUpdateView(LoginRequiredMixin, UpdateView):
    """
    View para editar relacionamento cliente-parceiro
    """
    model = ClientesParceiros
    form_class = NovoClienteForm
    template_name = 'editar_cliente.html'
    success_url = reverse_lazy('lista_clientes')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_initial(self):
        initial = super().get_initial()
        if self.object:
            initial['parceiro'] = self.object.id_company_base
            initial['cliente'] = self.object.id_company_vinculada
        return initial

# Views para AJAX (se necessário)
class EmpresasAjaxView(LoginRequiredMixin, View):
    """
    View para buscar empresas via AJAX
    """
    def get(self, request, *args, **kwargs):  # Somente GET (idempotente) – CSRF não é exigido para GET
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

class NovoParceiroView(UserPassesTestMixin, LoginRequiredMixin, CreateView):
    """Cadastro de novo parceiro (tipo_parceria='parceiro')."""
    model = ClientesParceiros
    form_class = NovoParceiroForm
    template_name = 'cadastrar_parceiro.html'
    success_url = reverse_lazy('lista_parceiros')

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['empresa_form'] = EmpresaForm(self.request.POST, self.request.FILES, prefix='empresa')
            context['contato_formset'] = ContatoFormSet(self.request.POST, initial=[{}])
        else:
            context['empresa_form'] = EmpresaForm(prefix='empresa')
            context['contato_formset'] = ContatoFormSet(initial=[{}])
        # Remover campo 'parceiro' se presente (vínculo já é fixo na view)
        if 'form' in context and 'parceiro' in context['form'].fields:
            context['form'].fields['parceiro'].widget = forms.HiddenInput()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        empresa_form = context['empresa_form']
        contato_formset = context['contato_formset']
        if form.is_valid() and empresa_form.is_valid() and contato_formset.is_valid():
            with transaction.atomic():
                empresa_parceiro = empresa_form.save()
                # Localiza empresa base fixa pelo CNPJ informado
                try:
                    parceiro_base = Empresa.objects.get(cnpj='42994794000104')
                except Empresa.DoesNotExist:
                    messages.error(self.request, 'Empresa base com CNPJ 42994794000104 não encontrada. Cadastre-a primeiro.')
                    return self.form_invalid(form)
                obj = ClientesParceiros(
                    id_company_base=parceiro_base,
                    id_company_vinculada=empresa_parceiro,
                    tipo_parceria='parceiro',
                    nome_referencia=form.cleaned_data['nome_referencia'],
                    cargo_referencia=form.cleaned_data['cargo_referencia']
                )
                obj.save()
                for contato_f in contato_formset:
                    if contato_f.cleaned_data and not contato_f.cleaned_data.get('DELETE', False):
                        c = contato_f.save(commit=False)
                        c.empresa_base = empresa_parceiro
                        c.save()
                messages.success(self.request, 'Parceiro cadastrado com sucesso!')
                return redirect(self.success_url)
        messages.error(self.request, 'Erros no formulário de parceiro.')
        return self.form_invalid(form)

class ParceiroDetailView(LoginRequiredMixin, View):
    template_name = 'parceiro_detail.html'
    def get(self, request, pk):
        qs = ClientesParceiros.objects.filter(tipo_parceria='parceiro')
        # Restringe para não-admin: somente registros cuja empresa base coincide com empresa_vinculada do perfil
        if not (request.user.is_staff or request.user.is_superuser):
            empresa_vinc = getattr(getattr(request.user, 'profile', None), 'empresa_vinculada', None)
            if not empresa_vinc:
                raise Http404
            qs = qs.filter(id_company_base=empresa_vinc)
        parceiro = get_object_or_404(qs, pk=pk)
        contatos = parceiro.id_company_vinculada.empresa_base_contato.all()
        return render(request, self.template_name, {
            'parceiro': parceiro,
            'contatos': contatos,
        })

class ClienteDetailView(LoginRequiredMixin, View):
    template_name = 'cliente_detail.html'
    def get(self, request, pk):
        qs = ClientesParceiros.objects.filter(tipo_parceria='cliente')
        if not (request.user.is_staff or request.user.is_superuser):
            profile = getattr(request.user, 'profile', None)
            empresa_vinc = getattr(profile, 'empresa_vinculada', None)
            if not empresa_vinc:
                raise Http404
            # Permite acesso se for parceiro (empresa base) ou cliente (empresa vinculada)
            # Caso de cliente: seu relacionamento onde é id_company_vinculada
            filtro = (
                models.Q(id_company_base=empresa_vinc) |
                models.Q(id_company_vinculada=empresa_vinc)
            )
            qs = qs.filter(filtro)
        cliente = get_object_or_404(qs, pk=pk)
        contatos = cliente.id_company_vinculada.empresa_base_contato.all()
        return render(request, self.template_name, {
            'cliente': cliente,
            'contatos': contatos,
        })

class EditarParceiroView(LoginRequiredMixin, UpdateView):
    model = ClientesParceiros
    form_class = NovoParceiroForm
    template_name = 'cadastrar_parceiro.html'
    success_url = reverse_lazy('lista_parceiros')

    def get_queryset(self):
        return ClientesParceiros.objects.filter(tipo_parceria='parceiro')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        if self.request.POST:
            context['empresa_form'] = EmpresaForm(self.request.POST, self.request.FILES, instance=obj.id_company_vinculada, prefix='empresa')
            contatos_qs = obj.id_company_vinculada.empresa_base_contato.all()
            context['contato_formset'] = ContatoFormSet(self.request.POST, initial=[{'tipo_contato': c.tipo_contato, 'telefone': c.telefone, 'email': c.email, 'site': c.site} for c in contatos_qs])
        else:
            context['empresa_form'] = EmpresaForm(instance=obj.id_company_vinculada, prefix='empresa')
            contatos_qs = obj.id_company_vinculada.empresa_base_contato.all()
            initial = [{'tipo_contato': c.tipo_contato, 'telefone': c.telefone, 'email': c.email, 'site': c.site} for c in contatos_qs]
            context['contato_formset'] = ContatoFormSet(initial=initial)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        empresa_form = context['empresa_form']
        contato_formset = context['contato_formset']
        if form.is_valid() and empresa_form.is_valid() and contato_formset.is_valid():
            with transaction.atomic():
                empresa = empresa_form.save()
                obj = form.save(commit=False)
                obj.id_company_vinculada = empresa
                obj.tipo_parceria = 'parceiro'
                obj.save()
                empresa.empresa_base_contato.all().delete()
                for contato_f in contato_formset:
                    if contato_f.cleaned_data and not contato_f.cleaned_data.get('DELETE', False):
                        c = contato_f.save(commit=False)
                        c.empresa_base = empresa
                        c.save()
                messages.success(self.request, 'Parceiro atualizado com sucesso!')
                return redirect(self.success_url)
        messages.error(self.request, 'Erros ao atualizar parceiro.')
        return self.form_invalid(form)

# Mantendo compatibilidade com URLs existentes
NewClienteParceiroView = NovoClienteView

# ================= DRF API Views =================

class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser

class ClientesParceirosListAPI(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        objetos = ClientesParceiros.objects.all()
        serializer = ClientesParceirosSerializer(objetos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ClientesParceirosCreateAPI(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        serializer = ClientesParceirosSerializer(data=request.data)
        if serializer.is_valid():
            try:
                obj = serializer.save()
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            out = ClientesParceirosSerializer(obj).data
            return Response(out, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClientesParceirosDetailAPI(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]

    def get_object(self, pk):
        try:
            return ClientesParceiros.objects.get(pk=pk)
        except ClientesParceiros.DoesNotExist:
            return None

    def get(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Registro não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ClientesParceirosSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Registro não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ClientesParceirosSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                obj = serializer.save()
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            return Response(ClientesParceirosSerializer(obj).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Registro não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
