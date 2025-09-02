from django.urls import path
from . import views

app_name = 'correcao'

urlpatterns = [
    # URLs para Correcao
    path('', views.CorrecaoListView.as_view(), name='list'),
    path('novo/', views.CorrecaoCreateView.as_view(), name='create'),
    path('editar/<int:pk>/', views.CorrecaoUpdateView.as_view(), name='update'),
    path('excluir/<int:pk>/', views.CorrecaoDeleteView.as_view(), name='delete'),
    # Histórico (padrão correto historico/<id>/)
    path('historico/<int:pk>/', views.correcao_history_json, name='history_json'),
    # Rota alternativa para chamadas já feitas no formato <id>/historico/ (fallback)
    path('<int:pk>/historico/', views.correcao_history_json, name='history_json_alt'),
    
    # URLs para tipoTese
    path('tipo-tese/', views.tipoTeseListView.as_view(), name='tipo_tese_list'),
    path('tipo-tese/novo/', views.tipoTeseCreateView.as_view(), name='tipo_tese_create'),
    path('tipo-tese/editar/<int:pk>/', views.tipoTeseUpdateView.as_view(), name='tipo_tese_update'),
    path('tipo-tese/excluir/<int:pk>/', views.tipoTeseDeleteView.as_view(), name='tipo_tese_delete'),
    path('tipo-tese/historico/<int:pk>/', views.tipo_tese_history_json, name='tipo_tese_history_json'),
    
    # URLs para TeseCredito
    path('tese-credito/', views.TeseCreditoListView.as_view(), name='tese_credito_list'),
    path('tese-credito/novo/', views.TeseCreditoCreateView.as_view(), name='tese_credito_create'),
    path('tese-credito/editar/<int:pk>/', views.TeseCreditoUpdateView.as_view(), name='tese_credito_update'),
    path('tese-credito/excluir/<int:pk>/', views.TeseCreditoDeleteView.as_view(), name='tese_credito_delete'),
    # Histórico Tese de Crédito
    path('tese-credito/historico/<int:pk>/', views.tese_credito_history_json, name='tese_credito_history_json'),

    # === API DRF padronizada ===
    # Correcao
    path('api/v1/listar-correcao/', views.CorrecaoListAPI.as_view(), name='api-correcao-list'),
    path('api/v1/criar-correcao/', views.CorrecaoCreateAPI.as_view(), name='api-correcao-create'),
    path('api/v1/listar-correcao/<int:pk>/', views.CorrecaoDetailAPI.as_view(), name='api-correcao-detail'),
    # tipoTese
    path('api/v1/listar-tipo-tese/', views.TipoTeseListAPI.as_view(), name='api-tipotese-list'),
    path('api/v1/criar-tipo-tese/', views.TipoTeseCreateAPI.as_view(), name='api-tipotese-create'),
    path('api/v1/listar-tipo-tese/<int:pk>/', views.TipoTeseDetailAPI.as_view(), name='api-tipotese-detail'),
    # TeseCredito
    path('api/v1/listar-tese-credito/', views.TeseCreditoListAPI.as_view(), name='api-tesecredito-list'),
    path('api/v1/criar-tese-credito/', views.TeseCreditoCreateAPI.as_view(), name='api-tesecredito-create'),
    path('api/v1/listar-tese-credito/<int:pk>/', views.TeseCreditoDetailAPI.as_view(), name='api-tesecredito-detail'),
]
