from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from accounts.decorators import cliente_can_view_lancamento, admin_required
from django.core.exceptions import ValidationError
from .models import Lancamentos, Anexos
from .forms import LancamentosForm, AnexosFormSet
from .permissions import LancamentoPermissionMixin, LancamentoClienteViewOnlyMixin, AdminRequiredMixin
from django.http import Http404

class LancamentosListView(LancamentoClienteViewOnlyMixin, ListView):
    model = Lancamentos
    template_name = 'lancamentos_list.html'
    context_object_name = 'lancamentos'
    paginate_by = 10
    
    def get_queryset(self):
        """
        Filtra os lançamentos por permissões e permite busca por PERDCOMP.
        """
        queryset = super().get_queryset().select_related('id_adesao').order_by('-data_lancamento')
        
        # Filtragem por permissões
        if self.request.user.is_superuser or self.request.user.is_staff:
            # Admins veem tudo
            pass
        elif hasattr(self.request.user, 'profile'):
            profile = self.request.user.profile
            
            # Para clientes, filtra diretamente pela empresa vinculada
            if profile.eh_cliente and profile.empresa_vinculada:
                queryset = queryset.filter(
                    id_adesao__cliente__id_company_vinculada=profile.empresa_vinculada
                )
                
            # Para parceiros, filtra pelas empresas acessíveis
            elif not profile.eh_cliente:
                empresas_acessiveis = profile.get_empresas_acessiveis()
                if empresas_acessiveis:
                    queryset = queryset.filter(
                        id_adesao__cliente__id_company_vinculada__in=empresas_acessiveis
                    )
                else:
                    return queryset.none()
            else:
                return queryset.none()
        else:
            return queryset.none()
        
        # Filtro por PERDCOMP
        perdcomp = self.request.GET.get('perdcomp')
        if perdcomp:
            queryset = queryset.filter(id_adesao__perdcomp__icontains=perdcomp)
            
        return queryset
        
    def get_context_data(self, **kwargs):
        """
        Adiciona parâmetros de filtro ao contexto para persistir a pesquisa na paginação.
        """
        context = super().get_context_data(**kwargs)
        context['current_filters'] = self.request.GET.dict()
        return context

class LancamentoDetailView(LancamentoClienteViewOnlyMixin, DetailView):
    model = Lancamentos
    template_name = 'lancamentos_detail.html'
    context_object_name = 'lancamento'
    
    def get_queryset(self):
        """
        Filtra o queryset para que clientes só vejam seus próprios lançamentos.
        """
        queryset = super().get_queryset()
        
        if self.request.user.is_superuser or self.request.user.is_staff:
            # Admins veem tudo
            return queryset
            
        if hasattr(self.request.user, 'profile'):
            profile = self.request.user.profile
            
            # Para clientes, filtra diretamente pela empresa vinculada
            if profile.eh_cliente and profile.empresa_vinculada:
                return queryset.filter(
                    id_adesao__cliente__id_company_vinculada=profile.empresa_vinculada
                )
                
            # Para parceiros, filtra pelas empresas acessíveis
            elif not profile.eh_cliente:
                empresas_acessiveis = profile.get_empresas_acessiveis()
                if empresas_acessiveis:
                    return queryset.filter(
                        id_adesao__cliente__id_company_vinculada__in=empresas_acessiveis
                    )
                    
        # Se chegou aqui, não tem acesso a nada
        return queryset.none()
    
    def get_object(self, queryset=None):
        """
        Verifica se o objeto existe no queryset filtrado.
        Se existir, permite o acesso. Caso contrário, mostra página de acesso negado.
        """
        if queryset is None:
            queryset = self.get_queryset()
            
        # Obtém o ID do objeto
        pk = self.kwargs.get(self.pk_url_kwarg)
        
        try:
            # Tenta obter o objeto do queryset filtrado
            obj = queryset.get(pk=pk)
            return obj
        except self.model.DoesNotExist:
            # Verifica se o objeto existe no banco, mas o usuário não tem permissão
            if self.model.objects.filter(pk=pk).exists():
                from django.shortcuts import render
                messages.error(self.request, "Você não tem permissão para visualizar este lançamento.")
                return render(
                    self.request, 
                    'forbidden.html', 
                    {'message': "Você não tem permissão para visualizar este lançamento."},
                    status=403
                )
            else:
                # Se não existe no banco, é um 404 legítimo
                raise Http404(f"Lançamento com ID {pk} não encontrado.")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['anexos'] = self.object.anexos.all()
        return context
        
class LancamentoCreateView(AdminRequiredMixin, CreateView):
    model = Lancamentos
    form_class = LancamentosForm
    template_name = 'lancamentos_form.html'
    success_url = reverse_lazy('lancamentos:list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['anexos_formset'] = AnexosFormSet(self.request.POST, self.request.FILES)
        else:
            context['anexos_formset'] = AnexosFormSet()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        anexos_formset = context['anexos_formset']
        
        try:
            with transaction.atomic():
                # Prepara o lançamento
                self.object = form.save(commit=False)
                
                # Limpa o objeto para que validações específicas sejam aplicadas
                self.object.clean()
                
                # Salva o lançamento (a validação já foi feita pelo clean())
                self.object.save()
                
                # Salva anexos
                if anexos_formset.is_valid():
                    anexos_formset.instance = self.object
                    anexos_formset.save()
                else:
                    return self.form_invalid(form)
                
                # Mensagem de sucesso
                messages.success(self.request, 'Lançamento cadastrado com sucesso!')
                return super().form_valid(form)
        
        except ValidationError as e:
            # Transfere erros de validação do modelo para o formulário
            for field, errors in e.message_dict.items():
                for error in errors:
                    form.add_error(field, error)
            messages.error(self.request, "Erro ao cadastrar lançamento. Verifique os campos.")
            return self.form_invalid(form)
        except Exception as e:
            # Log do erro para depuração
            import logging
            logging.error(f"Erro ao salvar lançamento: {str(e)}")
            messages.error(self.request, f"Erro ao processar lançamento: {str(e)}")
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao cadastrar lançamento. Verifique os campos.')
        return super().form_invalid(form)

# Removemos as views LancamentoUpdateView, LancamentoDeleteView e confirmar_lancamento
# já que lançamentos não podem mais ser editados ou excluídos

class AnexosUpdateView(AdminRequiredMixin, UpdateView):
    """View para editar apenas os anexos de um lançamento.
    
    Permite a edição de anexos, pois apenas os anexos são modificáveis
    após a criação do lançamento.
    """
    model = Lancamentos
    template_name = 'anexos_form.html'
    context_object_name = 'lancamento'
    
    def get_success_url(self):
        return reverse_lazy('lancamentos:detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['anexos_formset'] = AnexosFormSet(
                self.request.POST, 
                self.request.FILES, 
                instance=self.object
            )
        else:
            context['anexos_formset'] = AnexosFormSet(instance=self.object)
        
        # Adiciona uma flag para indicar que pode editar anexos sempre
        context['pode_editar_anexos'] = True
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        anexos_formset = AnexosFormSet(request.POST, request.FILES, instance=self.object)
        
        if anexos_formset.is_valid():
            with transaction.atomic():
                anexos_formset.save()
                messages.success(request, "Anexos atualizados com sucesso!")
                return redirect(self.get_success_url())
        else:
            return self.render_to_response(
                self.get_context_data(anexos_formset=anexos_formset)
            )


