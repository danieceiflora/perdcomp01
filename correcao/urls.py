from django.urls import path
from . import views

app_name = 'correcao'

urlpatterns = [
       
    
    # URLs para TeseCredito
    path('tese-credito/', views.TeseCreditoListView.as_view(), name='tese_credito_list'),
    path('tese-credito/novo/', views.TeseCreditoCreateView.as_view(), name='tese_credito_create'),
    path('tese-credito/editar/<int:pk>/', views.TeseCreditoUpdateView.as_view(), name='tese_credito_update'),
    path('tese-credito/excluir/<int:pk>/', views.TeseCreditoDeleteView.as_view(), name='tese_credito_delete'),
    # Histórico Tese de Crédito
    path('tese-credito/historico/<int:pk>/', views.tese_credito_history_json, name='tese_credito_history_json'),

    # === API DRF padronizada ===

    # tipoTese
    path('api/v1/listar-tipo-tese/', views.TipoTeseListAPI.as_view(), name='api-tipotese-list'),
    path('api/v1/criar-tipo-tese/', views.TipoTeseCreateAPI.as_view(), name='api-tipotese-create'),
    path('api/v1/listar-tipo-tese/<int:pk>/', views.TipoTeseDetailAPI.as_view(), name='api-tipotese-detail'),
    # TeseCredito
    path('api/v1/listar-tese-credito/', views.TeseCreditoListAPI.as_view(), name='api-tesecredito-list'),
    path('api/v1/criar-tese-credito/', views.TeseCreditoCreateAPI.as_view(), name='api-tesecredito-create'),
    path('api/v1/listar-tese-credito/<int:pk>/', views.TeseCreditoDetailAPI.as_view(), name='api-tesecredito-detail'),
]
