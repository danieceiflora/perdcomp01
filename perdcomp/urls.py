from django.contrib import admin
from django.urls import path, include
from empresas.views import home_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/', home_view, name='home'),
    path('', home_view),
    path('empresas/', include('empresas.urls')),
    path('contatos/', include('contatos.urls')),
    
]
