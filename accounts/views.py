from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import UserProfile
from utils.dashboard_access import build_dashboard_context, metricas_por_empresa, admin_counts, admin_metricas_globais
from django.http import JsonResponse, HttpResponseBadRequest

## Legacy login views removidas em favor de login unificado


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
    template_name = 'accounts/admin_login_tailwind.html'

    def get_success_url(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            # Pode redirecionar direto para /admin/ ou para dashboard unificado; opção: admin.
            return '/admin/'
        return reverse_lazy('accounts:dashboard')

    def form_valid(self, form):
        user = form.get_user()
        if user.is_staff or user.is_superuser:
            messages.success(self.request, f'Acesso administrativo: {user.username}')
        else:
            messages.success(self.request, 'Login efetuado com sucesso.')
        return super().form_valid(form)

class UnifiedDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        try:
            profile = user.profile
        except Exception:
            profile = None

        if profile:
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
        else:
            # Fallback para superuser/staff sem profile: visão administrativa genérica
            if user.is_superuser or user.is_staff:
                counts = admin_counts()
                metricas = admin_metricas_globais()
                # Coleta todas as empresas clientes distintas para permitir filtro
                from clientes_parceiros.models import ClientesParceiros
                clientes_ids = ClientesParceiros.objects.filter(
                    tipo_parceria='cliente', ativo=True
                ).values_list('id_company_vinculada_id', flat=True).distinct()
                from empresas.models import Empresa
                clientes_empresas = Empresa.objects.filter(id__in=clientes_ids)
                empresas_info = [
                    {'empresa': e, 'origem': 'cliente-global', 'is_base': False}
                    for e in clientes_empresas
                ]
                context.update({
                    'profile': None,
                    'tipo_usuario': 'Administrador',
                    'tipo_acesso': 'Administrador',
                    'empresas_total': counts['total_clientes'],
                    'credito_recuperado': metricas['credito_recuperado'],
                    'credito_utilizado': metricas['credito_utilizado'],
                    'saldo_credito': metricas['saldo_credito'],
                    'empresas_info': empresas_info,
                    'parceiro_base': None,
                    'total_parceiros': counts['total_parceiros'],
                    'total_clientes': counts['total_clientes'],
                })
            else:
                context.update({
                    'profile': None,
                    'tipo_usuario': 'Usuário',
                    'tipo_acesso': 'Usuário',
                    'empresas_total': 0,
                    'credito_recuperado': 0,
                    'credito_utilizado': 0,
                    'saldo_credito': 0,
                    'empresas_info': [],
                    'parceiro_base': None,
                })
        return context

class DashboardMetricsView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        try:
            profile = request.user.profile
        except Exception:
            profile = None
        empresa_id = request.GET.get('empresa')
        if profile:
            ctx = build_dashboard_context(profile)
            acessiveis_ids = {item['empresa'].id for item in ctx['empresas_info']}
            if empresa_id and empresa_id.isdigit():
                empresa_id_int = int(empresa_id)
                if empresa_id_int not in acessiveis_ids:
                    return HttpResponseBadRequest('Empresa não acessível.')
                m = metricas_por_empresa(empresa_id_int)
                return JsonResponse(m)
            return JsonResponse({
                'credito_recuperado': ctx['credito_recuperado'],
                'credito_utilizado': ctx['credito_utilizado'],
                'saldo_credito': ctx['saldo_credito']
            })
        # Sem profile: admin genérico ou usuário sem perfil -> métricas globais (se admin) ou zeros
        user = request.user
        if user.is_superuser or user.is_staff:
            from clientes_parceiros.models import ClientesParceiros
            if empresa_id and empresa_id.isdigit():
                empresa_id_int = int(empresa_id)
                # Verifica se é uma empresa cliente válida
                valido = ClientesParceiros.objects.filter(
                    id_company_vinculada_id=empresa_id_int,
                    tipo_parceria='cliente',
                    ativo=True
                ).exists()
                if not valido:
                    return HttpResponseBadRequest('Empresa não acessível.')
                m = metricas_por_empresa(empresa_id_int)
                return JsonResponse(m)
            metricas = admin_metricas_globais()
            return JsonResponse(metricas)
        return JsonResponse({'credito_recuperado': 0, 'credito_utilizado': 0, 'saldo_credito': 0})


@login_required
def user_profile_view(request):
    """Visualizar perfil do usuário"""
    profile = request.user.profile
    context = {
        'profile': profile,
        'user': request.user,
    }
    return render(request, 'accounts/profile.html', context)
