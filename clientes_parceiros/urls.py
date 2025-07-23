from django.urls import path
from clientes_parceiros import views
from .views import (
    NovoClienteView, NewClienteParceiroView, ListClienteParceiroView, 
    NewTipoRelacionamentoView, TipoRelacionamentoListView,
    TipoRelacionamentoUpdateView, ClienteParceiroUpdateView, EmpresasAjaxView
)

urlpatterns = [
    # Tipo de Relacionamento
    path('tipo-relacionamento/', NewTipoRelacionamentoView.as_view(), name='tipo_relacionamento'),
    path('tipo-relacionamento/editar/<int:pk>/', TipoRelacionamentoUpdateView.as_view(), name='editar_tipo_relacionamento'),
    path('tipo-relacionamento/listar/', TipoRelacionamentoListView.as_view(), name='lista_tipos_relacionamento'),
    
    # Cliente/Parceiro - Versão nova
    path('novo-cliente/', NovoClienteView.as_view(), name='novo_cliente'),
    
    # Cliente/Parceiro - Versões antigas (compatibilidade)
    path('cadastrar/', NewClienteParceiroView.as_view(), name='cadastrar_cliente_parceiro'),
    path('listar/', ListClienteParceiroView.as_view(), name='lista_clientes_parceiros'),
    path('editar/<int:pk>/', views.EditarClienteView.as_view(), name='editar_cliente_parceiro'),
    
    # AJAX
    path('ajax/empresas/', EmpresasAjaxView.as_view(), name='empresas_ajax'),
]