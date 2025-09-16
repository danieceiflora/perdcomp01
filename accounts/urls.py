from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'accounts'

urlpatterns = [
    # Seletor de login
    
    # Novo login unificado
    path('login/', views.UnifiedLoginView.as_view(), name='login'),

    # Novo dashboard unificado
    path('dashboard/', views.UnifiedDashboardView.as_view(), name='dashboard'),
    path('dashboard/metrics/', views.DashboardMetricsView.as_view(), name='dashboard_metrics'),
    
    # Rotas antigas apontando para login unificado (compatibilidade)
    # Legacy login redirects (to be removed after unification)
    
    
    # Perfil e logout
    path('profile/', views.user_profile_view, name='profile'),
    path('logout/', views.logout_view, name='logout'),
]
