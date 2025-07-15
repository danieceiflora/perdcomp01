from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Lancamentos, Anexos
from .forms import LancamentosForm, AnexosFormSet

class LancamentosListView(ListView):
    model = Lancamentos
    template_name = 'lancamentos/lancamentos_list.html'
    context_object_name = 'lancamentos'
    paginate_by = 10
    
    def get_queryset(self):
        """
        Retorna os lançamentos ordenados por data, com as adesões relacionadas carregadas
        para evitar consultas N+1 e otimizar a exibição do saldo atual.
        
        Permite filtrar por PERDCOMP se o parâmetro 'perdcomp' estiver na query string.
        """
        queryset = super().get_queryset().select_related('id_adesao').order_by('-data_lancamento')
        
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

class LancamentoDetailView(DetailView):
    model = Lancamentos
    template_name = 'lancamentos/lancamentos_detail.html'
    context_object_name = 'lancamento'
    
    def get_queryset(self):
        """
        Carrega a adesão relacionada para evitar consultas N+1 e 
        otimizar a exibição do saldo atual.
        """
        return super().get_queryset().select_related('id_adesao')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['anexos'] = self.object.anexos.all()
        return context

class LancamentoCreateView(CreateView):
    model = Lancamentos
    form_class = LancamentosForm
    template_name = 'lancamentos/lancamentos_form.html'
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
        
        with transaction.atomic():
            # Salva o lançamento
            self.object = form.save(commit=False)
            
            # Se o status for CONFIRMADO, registra a data de confirmação
            if self.object.status == 'CONFIRMADO':
                self.object.data_confirmacao = timezone.now()
            
            self.object.save()
            
            # Atualiza o saldo da adesão se o lançamento foi confirmado
            if self.object.status == 'CONFIRMADO':
                self.object.atualizar_saldo_adesao()
            
            # Salva os anexos se forem válidos
            if anexos_formset.is_valid():
                anexos_formset.instance = self.object
                anexos_formset.save()
            else:
                return self.form_invalid(form)
            
        status_msg = ""
        if self.object.status == 'CONFIRMADO':
            status_msg = " com status 'Confirmado'"
            
        messages.success(self.request, f'Lançamento cadastrado com sucesso{status_msg}!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao cadastrar lançamento. Verifique os campos.')
        return super().form_invalid(form)

class LancamentoUpdateView(UpdateView):
    model = Lancamentos
    form_class = LancamentosForm
    template_name = 'lancamentos/lancamentos_form.html'
    success_url = reverse_lazy('lancamentos:list')
    
    def dispatch(self, request, *args, **kwargs):
        """Verifica se o lançamento ainda pode ser editado"""
        self.object = self.get_object()
        if not self.object.pode_editar():
            messages.error(request, "Este lançamento não pode mais ser editado. Apenas os anexos podem ser modificados.")
            return redirect('lancamentos:editar_anexos', pk=self.object.pk)
        return super().dispatch(request, *args, **kwargs)
    
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
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        anexos_formset = context['anexos_formset']
        
        old_status = self.object.status
        new_status = form.cleaned_data.get('status')
        
        with transaction.atomic():
            self.object = form.save(commit=False)
            
            # Se o status mudou para CONFIRMADO, registra a data de confirmação
            if old_status != 'CONFIRMADO' and new_status == 'CONFIRMADO':
                self.object.data_confirmacao = timezone.now()
                
            self.object.save()
            
            # Atualiza o saldo da adesão se o status foi alterado para ou de CONFIRMADO
            if (old_status != 'CONFIRMADO' and new_status == 'CONFIRMADO') or \
               (old_status == 'CONFIRMADO' and new_status != 'CONFIRMADO'):
                # Se o lançamento agora está confirmado, atualizamos o saldo
                if new_status == 'CONFIRMADO':
                    self.object.atualizar_saldo_adesao()
                # Se estava confirmado e agora não está, revertemos o efeito no saldo
                else:
                    # Invertemos o sinal para reverter o efeito anterior
                    original_sinal = self.object.sinal
                    self.object.sinal = '+' if original_sinal == '-' else '-'
                    self.object.atualizar_saldo_adesao()
                    # Restauramos o sinal original
                    self.object.sinal = original_sinal
                    self.object.save(update_fields=['sinal'])
            
            if anexos_formset.is_valid():
                anexos_formset.instance = self.object
                anexos_formset.save()
            else:
                return self.form_invalid(form)
                
        if old_status != new_status:
            messages.success(self.request, f'Status do lançamento alterado para {self.object.get_status_display()}!')
        else:
            messages.success(self.request, 'Lançamento atualizado com sucesso!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao atualizar lançamento. Verifique os campos.')
        return super().form_invalid(form)

class LancamentoDeleteView(DeleteView):
    model = Lancamentos
    template_name = 'lancamentos/lancamentos_confirm_delete.html'
    success_url = reverse_lazy('lancamentos:list')
    context_object_name = 'lancamento'
    
    def dispatch(self, request, *args, **kwargs):
        """Verifica se o lançamento pode ser excluído"""
        self.object = self.get_object()
        if not self.object.pode_excluir():
            messages.error(request, "Este lançamento não pode ser excluído pois já foi confirmado.")
            return redirect('lancamentos:detail', pk=self.object.pk)
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Lançamento excluído com sucesso!')
        return super().delete(request, *args, **kwargs)

@login_required
def confirmar_lancamento(request, pk):
    """Confirma um lançamento, tornando-o não mais editável.
    Essa view ainda é mantida para compatibilidade com os links de confirmação
    existentes e para permitir confirmar rapidamente sem editar o lançamento.
    
    Ao confirmar o lançamento, o saldo atual da adesão é atualizado de acordo
    com o valor e sinal do lançamento.
    """
    lancamento = get_object_or_404(Lancamentos, pk=pk)
    
    if lancamento.status != 'PENDENTE':
        messages.error(request, "Este lançamento já foi confirmado ou estornado.")
        return redirect('lancamentos:detail', pk=pk)
    
    with transaction.atomic():
        lancamento.status = 'CONFIRMADO'
        lancamento.data_confirmacao = timezone.now()
        lancamento.save()
        
        # Atualiza o saldo da adesão
        lancamento.atualizar_saldo_adesao()
        
        messages.success(request, "Lançamento confirmado com sucesso!")
    
    return redirect('lancamentos:detail', pk=pk)

class AnexosUpdateView(LoginRequiredMixin, UpdateView):
    """View para editar apenas os anexos de um lançamento.
    
    Permite a edição de anexos mesmo para lançamentos que já foram confirmados
    ou estornados, pois apenas os anexos são modificáveis após a confirmação.
    
    Para lançamentos no status PENDENTE, também é possível editar os dados do
    lançamento pela view de edição normal.
    """
    model = Lancamentos
    template_name = 'lancamentos/anexos_form.html'
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

@login_required
def estornar_lancamento(request, pk):
    """Cria um estorno para um lançamento."""
    lancamento = get_object_or_404(Lancamentos, pk=pk)
    
    if lancamento.status != 'CONFIRMADO':
        messages.error(request, "Apenas lançamentos confirmados podem ser estornados.")
        return redirect('lancamentos:detail', pk=pk)
    
    # Verifica se já existe um estorno para este lançamento
    if Lancamentos.objects.filter(lancamento_original=lancamento).exists():
        messages.error(request, "Este lançamento já possui um estorno.")
        return redirect('lancamentos:detail', pk=pk)
    
    with transaction.atomic():
        # Marca o lançamento original como estornado
        lancamento.status = 'ESTORNADO'
        
        # Revertemos o efeito do lançamento original no saldo
        # Invertemos o sinal para reverter o efeito anterior
        original_sinal = lancamento.sinal
        lancamento.sinal = '+' if original_sinal == '-' else '-'
        lancamento.atualizar_saldo_adesao()
        # Restauramos o sinal original
        lancamento.sinal = original_sinal
        
        lancamento.save()
        
        # Cria o lançamento de estorno com sinal contrário
        estorno = Lancamentos(
            id_adesao=lancamento.id_adesao,
            data_lancamento=timezone.now().date(),
            valor=lancamento.valor,
            sinal='+' if lancamento.sinal == '-' else '-',
            tipo=lancamento.tipo,
            observacao=f"Estorno do lançamento #{lancamento.id}",
            status='CONFIRMADO',
            data_confirmacao=timezone.now(),
            lancamento_original=lancamento
        )
        estorno.save()
        
        # Atualizamos o saldo com o lançamento de estorno
        estorno.atualizar_saldo_adesao()
        
        messages.success(request, "Lançamento estornado com sucesso!")
    
    return redirect('lancamentos:detail', pk=estorno.pk)
