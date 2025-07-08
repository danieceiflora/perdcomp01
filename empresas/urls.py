from django.urls import path
from empresas.views import NewEmpresaView, EmpresaListView, EmpresaUpdateView

urlpatterns = [
  path('cadastro_empresa/', NewEmpresaView.as_view(), name='cadastro_empresa'),
  path('lista-empresas/', EmpresaListView.as_view(), name='empresas'),
  path('editar-empresa/<int:pk>/', EmpresaUpdateView.as_view(), name='editar_empresa'),
]