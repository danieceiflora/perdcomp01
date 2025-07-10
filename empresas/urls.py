from django.urls import path
from empresas.views import NewEmpresaView, EmpresaListView, EmpresaUpdateView

app_name = 'empresas'  # Add this line to register the namespace

urlpatterns = [
  path('cadastro_empresa/', NewEmpresaView.as_view(), name='cadastro_empresa'),
  path('lista_empresas/', EmpresaListView.as_view(), name='lista_empresas'),  # Changed from 'empresas' to 'lista-empresas'
  path('editar_empresa/<int:pk>/', EmpresaUpdateView.as_view(), name='editar_empresa'),
]