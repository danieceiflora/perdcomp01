from django.urls import path
from . import views

app_name = 'correcao'

urlpatterns = [
       
    
    # URLs para TeseCredito
    path('tipo-documento/', views.TeseCreditoListView.as_view(), name='tipo_documento_list'),
    path('tipo-documento/novo/', views.TeseCreditoCreateView.as_view(), name='tipo_documento_create'),
    path('tipo-documento/editar/<int:pk>/', views.TeseCreditoUpdateView.as_view(), name='tipo_documento_update'),
    path('tipo-documento/excluir/<int:pk>/', views.TeseCreditoDeleteView.as_view(), name='tipo_documento_delete'),
    # Histórico Tese de Crédito
    path('tipo-documento/historico/<int:pk>/', views.tipo_documento_history_json, name='tipo_documento_history_json'),

    # TeseCredito
    path('api/v1/listar-tipo-documento/', views.TeseCreditoListAPI.as_view(), name='api-tesecredito-list'),
    path('api/v1/criar-tipo-documento/', views.TeseCreditoCreateAPI.as_view(), name='api-tesecredito-create'),
    path('api/v1/listar-tipo-documento/<int:pk>/', views.TeseCreditoDetailAPI.as_view(), name='api-tesecredito-detail'),
]
