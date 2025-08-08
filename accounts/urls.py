from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Seletor de login
    path('', views.LoginSelectorView.as_view(), name='login_selector'),
    
    # Login administrativo
    path('admin-login/', views.AdminLoginView.as_view(), name='admin_login'),
    
    # Login específico por tipo
    path('cliente/login/', views.ClienteLoginView.as_view(), name='cliente_login'),
    path('parceiro/login/', views.ParceiroLoginView.as_view(), name='parceiro_login'),
    
    # Dashboards
    path('cliente/dashboard/', views.ClienteDashboardView.as_view(), name='cliente_dashboard'),
    path('parceiro/dashboard/', views.ParceiroDashboardView.as_view(), name='parceiro_dashboard'),
    
    # Perfil e logout
    path('profile/', views.user_profile_view, name='profile'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
]
