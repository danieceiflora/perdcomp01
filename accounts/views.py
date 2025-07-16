from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import UserProfile

class ClienteLoginView(LoginView):
    template_name = 'accounts/cliente/login.html'
    
    def get_success_url(self):
        return reverse_lazy('accounts:cliente_dashboard')
    
    def form_valid(self, form):
        user = form.get_user()
        # Verificar se usuário tem perfil de cliente
        try:
            profile = user.profile
            if not profile.eh_cliente:
                messages.error(self.request, 'Este usuário não tem permissão de cliente.')
                return self.form_invalid(form)
        except UserProfile.DoesNotExist:
            messages.error(self.request, 'Perfil de usuário não encontrado.')
            return self.form_invalid(form)
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Usuário ou senha inválidos. Por favor, tente novamente.')
        return super().form_invalid(form)

class ParceiroLoginView(LoginView):
    template_name = 'accounts/parceiro/login.html'
    
    def get_success_url(self):
        return reverse_lazy('accounts:parceiro_dashboard')
    
    def form_valid(self, form):
        user = form.get_user()
        # Verificar se usuário tem perfil de parceiro
        try:
            profile = user.profile
            if not profile.eh_parceiro:
                messages.error(self.request, 'Este usuário não tem permissão de parceiro.')
                return self.form_invalid(form)
        except UserProfile.DoesNotExist:
            messages.error(self.request, 'Perfil de usuário não encontrado.')
            return self.form_invalid(form)
        
        return super().form_valid(form)

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('accounts:cliente_login')
    
    def dispatch(self, request, *args, **kwargs):
        # Captura o nome do usuário antes de fazer logout
        user_name = request.user.get_full_name() or request.user.username if request.user.is_authenticated else "Visitante"
        
        # Adiciona mensagem de feedback antes de fazer logout
        if request.user.is_authenticated:
            messages.success(request, f'Até logo, {user_name}! Você saiu do sistema com sucesso.')
        
        # Faz o logout e redireciona diretamente
        from django.contrib.auth import logout
        logout(request)
        
        # Redireciona diretamente para a página de login do cliente
        return redirect('accounts:cliente_login')

class LoginSelectorView(TemplateView):
    template_name = 'accounts/login_selector.html'

class ClienteDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/cliente/dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.profile.eh_cliente:
            messages.error(request, 'Acesso negado. Você não tem permissão de cliente.')
            return redirect('accounts:login_selector')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.profile
        
        # Importa o modelo necessário
        from clientes_parceiros.models import ClientesParceiros
        
        # Esclarecendo:
        # - O usuário cliente está vinculado a uma empresa que é cliente de algum parceiro
        # - Para um cliente, só mostramos a própria empresa
        # - Na tabela clientes_parceiros, esta empresa aparece como id_company_vinculada
        #   onde o tipo_relacionamento é "Cliente"
        
        # Para clientes, apenas a própria empresa é acessível
        empresas_acessiveis = [profile.empresa_vinculada]
        
        # Encontra o relacionamento com o parceiro
        relacionamento_com_parceiro = ClientesParceiros.objects.filter(
            id_company_vinculada=profile.empresa_vinculada,
            id_tipo_relacionamento__tipo_relacionamento__icontains='cliente',
            ativo=True
        ).select_related('id_company_base', 'id_tipo_relacionamento').first()
        
        # Informações sobre o parceiro que atende este cliente (se existir)
        parceiro_info = None
        if relacionamento_com_parceiro:
            parceiro_info = {
                'empresa': relacionamento_com_parceiro.id_company_base,
                'nome_referencia': relacionamento_com_parceiro.nome_referencia,
                'cargo_referencia': relacionamento_com_parceiro.cargo_referencia,
                'data_inicio': relacionamento_com_parceiro.data_inicio_parceria
            }
        
        context.update({
            'profile': profile,
            'empresa': profile.empresa_vinculada,  # Empresa do cliente logado
            'tipo_acesso': 'Cliente',
            'empresas_acessiveis': empresas_acessiveis,  # Apenas a própria empresa
            'parceiro_info': parceiro_info,  # Informações sobre o parceiro que atende este cliente
        })
        return context

class ParceiroDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/parceiro/dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.profile.eh_parceiro:
            messages.error(request, 'Acesso negado. Você não tem permissão de parceiro.')
            return redirect('accounts:login_selector')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.profile
        
        # Importa o modelo necessário
        from clientes_parceiros.models import ClientesParceiros
        
        # CORREÇÃO DA ESTRUTURA HIERÁRQUICA:
        # 1. Empresa principal (empresa no sistema)
        # 2. Parceiros (vários por empresa)
        # 3. Clientes (vários por parceiro)
        #
        # O usuário parceiro está vinculado a uma empresa que é parceira da empresa principal
        # A empresa do parceiro está como empresa_vinculada em seu registro de relacionamento
        # Os clientes deste parceiro estão em outros registros onde:
        # - A id_company_base é a empresa do parceiro (empresa_vinculada do perfil)
        # - O tipo de relacionamento contém "cliente"
        
        # Filtra todos os relacionamentos onde:
        # - A empresa base é a empresa vinculada ao usuário parceiro (empresa do parceiro)
        # - O tipo de relacionamento é "Cliente" (ou contém "cliente")
        # - O relacionamento está ativo
        clientes_relacionamentos = ClientesParceiros.objects.filter(
            id_company_base=profile.empresa_vinculada,  # Empresa do parceiro (empresa_vinculada no perfil)
            id_tipo_relacionamento__tipo_relacionamento__icontains='cliente',  # Relacionamento tipo Cliente
            ativo=True  # Apenas relacionamentos ativos
        ).select_related('id_company_vinculada', 'id_tipo_relacionamento')
        
        # Lista de empresas clientes (id_company_vinculada são as empresas clientes)
        empresas_clientes = [rel.id_company_vinculada for rel in clientes_relacionamentos]
        
        # Informações detalhadas dos relacionamentos para uso no template
        relacionamentos_info = [{
            'empresa': rel.id_company_vinculada,
            'tipo_relacionamento': rel.id_tipo_relacionamento.tipo_relacionamento,
            'nome_referencia': rel.nome_referencia,
            'cargo_referencia': rel.cargo_referencia,
            'data_inicio': rel.data_inicio_parceria,
            'ativo': rel.ativo
        } for rel in clientes_relacionamentos]
        
        # Recupera informações sobre a empresa principal (empresa que o parceiro está vinculado)
        empresa_principal = profile.empresa_base
        
        context.update({
            'profile': profile,
            'empresa': profile.empresa_vinculada,  # Empresa do parceiro (a que aparece no dashboard)
            'empresa_principal': empresa_principal,  # Empresa principal do sistema
            'tipo_acesso': 'Parceiro',
            'empresas_acessiveis': empresas_clientes,  # Lista de empresas clientes vinculadas ao parceiro
            'relacionamentos_info': relacionamentos_info,  # Detalhes dos relacionamentos
            'total_clientes': len(empresas_clientes),
        })
        return context

@login_required
def user_profile_view(request):
    """Visualizar perfil do usuário"""
    profile = request.user.profile
    context = {
        'profile': profile,
        'user': request.user,
    }
    return render(request, 'accounts/profile.html', context)
