from django.urls import path
from clientes_parceiros import views
from .views import NewClienteParceiroView, ListClienteParceiroView, NewTipoRelacionamentoView, TipoRelacionamentoListView
from .views import TipoRelacionamentoUpdateView, TipoRelacionamentoDeleteView
urlpatterns = [
    path('tipo-relacionamento/', NewTipoRelacionamentoView.as_view(), name='tipo_relacionamento'),
    path('tipo-relacionamento/editar/<int:pk>/', TipoRelacionamentoUpdateView.as_view(), name='editar_tipo_relacionamento'),
    path('tipo-relacionamento/listar/', TipoRelacionamentoListView.as_view(), name='lista_tipos_relacionamento'),
    path('tipo-relacionamento/excluir/<int:pk>/', TipoRelacionamentoDeleteView.as_view(), name='excluir_tipo_relacionamento'),
    path('cadastrar/', NewClienteParceiroView.as_view(), name='cadastrar_cliente_parceiro'),
    path('listar/', ListClienteParceiroView.as_view(), name='lista_clientes_parceiros'),
]