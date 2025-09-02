from django.urls import path
from clientes_parceiros import views
from .views import (
    NovoClienteView, NewClienteParceiroView, ListClienteParceiroView, EmpresasAjaxView,
    NovoParceiroView, ParceiroDetailView, EditarParceiroView, ListParceirosView,
    ClienteDetailView, clientes_parceiros_history_json,
    ClientesParceirosListAPI, ClientesParceirosCreateAPI, ClientesParceirosDetailAPI
)

urlpatterns = [
   
    # Cliente/Parceiro - Versão nova
    path('novo-cliente/', NovoClienteView.as_view(), name='novo_cliente'),
    
    # Cliente/Parceiro - Versões antigas (compatibilidade)
    path('cliente/novo/', NewClienteParceiroView.as_view(), name='novo_cliente'),
    path('clientes/', ListClienteParceiroView.as_view(), name='lista_clientes'),
    path('cliente/<int:pk>/editar/', views.EditarClienteView.as_view(), name='editar_cliente'),
    
    # AJAX
    path('ajax/empresas/', EmpresasAjaxView.as_view(), name='empresas_ajax'),
    path('empresas-disponiveis-ajax/<int:tipo_id>/', views.empresas_disponiveis_ajax, name='empresas_disponiveis_ajax'),
    
    # Parceiro
    path('parceiro/novo/', NovoParceiroView.as_view(), name='novo_parceiro'),
    path('parceiros/', ListParceirosView.as_view(), name='lista_parceiros'),
    path('parceiro/<int:pk>/', ParceiroDetailView.as_view(), name='detalhe_parceiro'),
    path('parceiro/<int:pk>/editar/', EditarParceiroView.as_view(), name='editar_parceiro'),
    # Histórico JSON (cliente ou parceiro)
    path('historico/<int:pk>/', clientes_parceiros_history_json, name='clientes_parceiros_history_json'),
    
    # Cliente - Detalhe
    path('cliente/<int:pk>/', ClienteDetailView.as_view(), name='cliente_detail'),

    # === API DRF ===
    path('api/v1/listar-clientes-parceiros/', ClientesParceirosListAPI.as_view(), name='api-clientes-parceiros-list'),
    path('api/v1/criar-clientes-parceiros/', ClientesParceirosCreateAPI.as_view(), name='api-clientes-parceiros-create'),
    path('api/v1/listar-clientes-parceiros/<int:pk>/', ClientesParceirosDetailAPI.as_view(), name='api-clientes-parceiros-detail'),
]