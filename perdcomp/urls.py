from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from empresas.views import home_view
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from perdcomp.views import token_jwt_view
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import LoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    # Redireciona /home para /admin-login/
    path('home/', RedirectView.as_view(pattern_name='admin-login', permanent=False), name='home'),
    # Alias amigável que leva à tela de login do admin
    path('admin-login/', RedirectView.as_view(url='/accounts/admin-login'), name='admin-login'),
    path('', RedirectView.as_view(pattern_name='admin-login', permanent=False)),
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
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
