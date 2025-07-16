from django.contrib import admin
from django.urls import path, include
from empresas.views import home_view
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('home/', home_view, name='home'),
    path('', home_view),
    path('empresas/', include('empresas.urls')),
    path('contatos/', include('contatos.urls')),
    path('clientes-parceiros/', include('clientes_parceiros.urls')),
    path('correcoes/', include('correcao.urls')),
    path('adesoes/', include('adesao.urls')),
    path('lancamentos/', include('lancamentos.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
