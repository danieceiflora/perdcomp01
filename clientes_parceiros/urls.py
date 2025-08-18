from django.urls import path
from clientes_parceiros import views
from .views import (
    NovoClienteView, NewClienteParceiroView, ListClienteParceiroView, EmpresasAjaxView,
    NovoParceiroView, ParceiroDetailView, EditarParceiroView
)

urlpatterns = [
   
    # Cliente/Parceiro - Versão nova
    path('novo-cliente/', NovoClienteView.as_view(), name='novo_cliente'),
    
    # Cliente/Parceiro - Versões antigas (compatibilidade)
    path('cadastrar/', NewClienteParceiroView.as_view(), name='cadastrar_cliente_parceiro'),
    path('listar/', ListClienteParceiroView.as_view(), name='lista_clientes_parceiros'),
    path('editar/<int:pk>/', views.EditarClienteView.as_view(), name='editar_cliente_parceiro'),
    
    # AJAX
    path('ajax/empresas/', EmpresasAjaxView.as_view(), name='empresas_ajax'),
    path('empresas-disponiveis-ajax/<int:tipo_id>/', views.empresas_disponiveis_ajax, name='empresas_disponiveis_ajax'),
    
    # Parceiro
    path('parceiro/novo/', NovoParceiroView.as_view(), name='novo_parceiro'),
    path('parceiro/<int:pk>/', ParceiroDetailView.as_view(), name='detalhe_parceiro'),
    path('parceiro/<int:pk>/editar/', EditarParceiroView.as_view(), name='editar_parceiro'),
]