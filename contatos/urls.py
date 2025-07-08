from django.contrib import admin
from django.urls import path, include
from empresas.views import home_view, NewEmpresaView, EmpresaListView, EmpresaUpdateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cadastro_empresa/', NewEmpresaView.as_view(), name='cadastro_empresa'),
    path('lista-empresas/', EmpresaListView.as_view(), name='empresas'),
    path('editar-empresa/<int:pk>/', EmpresaUpdateView.as_view(), name='editar_empresa'),
]
