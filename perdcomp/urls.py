from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from empresas.views import home_view
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from perdcomp.views import token_jwt_view, selic_acumulada_view, importacao_logs_page
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest

# Ajusta o link "Ver o site" do admin para levar ao dashboard unificado
admin.site.site_url = '/accounts/dashboard/'

def root_view(request: HttpRequest):
    """Rota raiz:
    - Usuário autenticado (não staff): dashboard unificado
    - Usuário staff/superuser: permanece no admin se veio de lá, mas se acessa '/', envia ao dashboard (pode ajustar se preferir admin)
    - Anônimo: login unificado
    """
    if request.user.is_authenticated:
        # Se desejar que staff vá para /admin/ em vez de dashboard, trocar linha abaixo
        return redirect('accounts:dashboard')
    return redirect('accounts:login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', root_view, name='root'),
    path('logs-importacao/', importacao_logs_page, name='importacao_logs'),
    path('empresas/', include('empresas.urls')),
    path('contatos/', include('contatos.urls')),
    path('clientes-parceiros/', include('clientes_parceiros.urls')),
    path('correcoes/', include('correcao.urls')),
    path('adesoes/', include('adesao.urls')),
    path('lancamentos/', include('lancamentos.urls')),
    path('dashboard/', include('dashboard.urls')),
    # JWT endpoints no app principal
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token-jwt/', token_jwt_view, name='token-jwt'),
    # Schema & Docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # API utilitária
    path('api/selic-acumulada/', selic_acumulada_view, name='selic-acumulada'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
