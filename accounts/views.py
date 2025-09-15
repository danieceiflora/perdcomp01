from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import UserProfile
from utils.dashboard_access import build_dashboard_context, metricas_por_empresa
from django.http import JsonResponse, HttpResponseBadRequest

class AdminLoginView(LoginView):
    """
    View de login para usuários administrativos (staff/superuser)
    """
    template_name = 'accounts/admin_login_tailwind.html'
    
    def get_success_url(self):
        # Redireciona para o dashboard administrativo ou home
        return reverse_lazy('dashboard:dashboard')  # ou 'home' se preferir
    
    def form_valid(self, form):
        user = form.get_user()
        
        # Verificar se usuário é staff ou superuser
        if not (user.is_staff or user.is_superuser):
            messages.error(self.request, 'Acesso negado. Este login é restrito a administradores do sistema.')
            return self.form_invalid(form)
        
        messages.success(self.request, f'Bem-vindo ao painel administrativo, {user.first_name or user.username}!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Usuário ou senha inválidos.')
        return super().form_invalid(form)
    
    def dispatch(self, request, *args, **kwargs):
        # Se já está logado e é admin, redireciona para dashboard
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            return redirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

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
        messages.error(self.request, 'Usuário ou senha inválidos.')
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
    
    def form_invalid(self, form):
        messages.error(self.request, 'Usuário ou senha inválidos.')
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
     
    def dispatch(self, request, *args, **kwargs):
        # Determina para onde redirecionar após o logout com base no tipo de usuário
        redirect_url = 'accounts:login_selector'  # Padrão: seletor de login
        
        if request.user.is_authenticated:
            try:
                # Verifica o tipo de usuário antes de fazer logout
                profile = request.user.profile
                
                if profile.eh_parceiro:
                    redirect_url = 'accounts:login_selector'
                elif profile.eh_cliente:
                    redirect_url = 'accounts:cliente_login'
            except Exception:
                # Se houver algum erro, usa o redirecionamento padrão
                pass
        
        # Faz o logout
        from django.contrib.auth import logout
        logout(request)
        
        # Redireciona com base no tipo de usuário
        return redirect(redirect_url)

class LoginSelectorView(TemplateView):
    template_name = 'accounts/login_selector.html'

class UnifiedLoginView(LoginView):
    template_name = 'accounts/login.html'

    def get_success_url(self):
        return reverse_lazy('accounts:dashboard')

    def form_valid(self, form):
        messages.success(self.request, 'Login efetuado com sucesso.')
        return super().form_valid(form)

class UnifiedDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.profile
        ctx = build_dashboard_context(profile)
        context.update({
            'profile': profile,
            'tipo_usuario': ctx['tipo_usuario'],
            'tipo_acesso': ctx['tipo_usuario'],
            'empresas_total': ctx['empresas_total'],
            'credito_recuperado': ctx['credito_recuperado'],
            'credito_utilizado': ctx['credito_utilizado'],
            'saldo_credito': ctx['saldo_credito'],
            'empresas_info': ctx['empresas_info'],
            'parceiro_base': ctx.get('parceiro_base'),
        })
        return context

class DashboardMetricsView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        profile = request.user.profile
        empresa_id = request.GET.get('empresa')
        # Coleta empresas acessíveis (exceto parceiro-base)
        ctx = build_dashboard_context(profile)
        acessiveis_ids = {item['empresa'].id for item in ctx['empresas_info']}
        if empresa_id and empresa_id.isdigit():
            empresa_id_int = int(empresa_id)
            if empresa_id_int not in acessiveis_ids:
                return HttpResponseBadRequest('Empresa não acessível.')
            m = metricas_por_empresa(empresa_id_int)
            return JsonResponse(m)
        # Sem empresa: retorna agregadas já calculadas
        return JsonResponse({
            'credito_recuperado': ctx['credito_recuperado'],
            'credito_utilizado': ctx['credito_utilizado'],
            'saldo_credito': ctx['saldo_credito']
        })

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
        
        # Importa os modelos necessários
        from clientes_parceiros.models import ClientesParceiros
        from lancamentos.models import Lancamentos
        from django.db.models import Sum
        from django.utils import timezone
        
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
            tipo_parceria='cliente',
            ativo=True
        ).select_related('id_company_base').first()
        
        # Informações sobre o parceiro que atende este cliente (se existir)
        parceiro_info = None
        if relacionamento_com_parceiro:
            parceiro_info = {
                'empresa': relacionamento_com_parceiro.id_company_base,
                'nome_referencia': relacionamento_com_parceiro.nome_referencia,
                'cargo_referencia': relacionamento_com_parceiro.cargo_referencia,
                'data_inicio': relacionamento_com_parceiro.data_inicio_parceria
            }
        
        # Calcular as métricas para este cliente
        from adesao.models import Adesao
        
        credito_recuperado = 0
        credito_utilizado = 0
        saldo_credito = 0
        
        if relacionamento_com_parceiro:
            # Buscar todas as adesões do cliente
            adesoes_cliente = Adesao.objects.filter(
                cliente=relacionamento_com_parceiro
            )
            
            # 1. Crédito Recuperado: Soma do valor inicial de todas as adesões
            credito_recuperado = adesoes_cliente.aggregate(
                total=Sum('saldo')
            )['total'] or 0
            
            # 2. Crédito Utilizado: Total de lançamentos com sinal='-' nas adesões do cliente
            credito_utilizado_resultado = Lancamentos.objects.filter(
                id_adesao__in=adesoes_cliente,
                sinal='-'  # Débito representa crédito utilizado
            ).aggregate(total=Sum('valor'))['total'] or 0
            
            # Como os valores de débito são negativos, pegamos o valor absoluto
            credito_utilizado = abs(credito_utilizado_resultado)
            
            # 3. Saldo de Crédito: Soma dos saldos atuais de todas as adesões
            saldo_credito = adesoes_cliente.aggregate(
                total=Sum('saldo_atual')
            )['total'] or 0
            
            # Garante que os valores sejam não-negativos
            credito_recuperado = max(0, credito_recuperado)
            saldo_credito = max(0, saldo_credito)
        
        context.update({
            'profile': profile,
            'empresa': profile.empresa_vinculada,  # Empresa do cliente logado
            'tipo_acesso': 'Cliente',
            'empresas_acessiveis': empresas_acessiveis,  # Apenas a própria empresa
            'parceiro_info': parceiro_info,  # Informações sobre o parceiro que atende este cliente
            'credito_recuperado': credito_recuperado,  # Total inicial das adesões
            'credito_utilizado': credito_utilizado,    # Total de lançamentos de débito
            'saldo_credito': saldo_credito,           # Saldo atual das adesões
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
            id_company_base=profile.empresa_vinculada,
            tipo_parceria='cliente',
            ativo=True
        ).select_related('id_company_vinculada')
        
        # Lista de empresas clientes (id_company_vinculada são as empresas clientes)
        empresas_clientes = [rel.id_company_vinculada for rel in clientes_relacionamentos]
        
        # Informações detalhadas dos relacionamentos para uso no template
        relacionamentos_info = [{
            'empresa': rel.id_company_vinculada,
            'tipo_relacionamento': rel.tipo_parceria,
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
