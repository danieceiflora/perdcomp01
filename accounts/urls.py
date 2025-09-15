from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'accounts'

urlpatterns = [
    # Seletor de login
    path('', views.LoginSelectorView.as_view(), name='login_selector'),

    # Novo login unificado
    path('login/', views.UnifiedLoginView.as_view(), name='login'),

    # Novo dashboard unificado
    path('dashboard/', views.UnifiedDashboardView.as_view(), name='dashboard'),
    path('dashboard/metrics/', views.DashboardMetricsView.as_view(), name='dashboard_metrics'),
    
    # Login administrativo
    path('admin-login/', views.AdminLoginView.as_view(), name='admin_login'),
    
    # Login específico por tipo
    path('cliente/login/', views.ClienteLoginView.as_view(), name='cliente_login'),
    path('parceiro/login/', views.ParceiroLoginView.as_view(), name='parceiro_login'),
    
    # Dashboards antigos (temporário: redirecionar para unificado)
    path('cliente/dashboard/', lambda r: redirect('accounts:dashboard'), name='cliente_dashboard'),
    path('parceiro/dashboard/', lambda r: redirect('accounts:dashboard'), name='parceiro_dashboard'),
    
    # Perfil e logout
    path('profile/', views.user_profile_view, name='profile'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
]
