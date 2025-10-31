from django.urls import path
from . import views


app_name = 'adesao'
##teste

urlpatterns = [
    path('', views.AdesaoListView.as_view(), name='list'),
    path('novo/', views.AdesaoCreateView.as_view(), name='create'),
    path('editar/<int:pk>/', views.AdesaoUpdateView.as_view(), name='update'),
    path('detalhe/<int:pk>/', views.AdesaoDetailView.as_view(), name='detail'),
    path('historico/<int:pk>/', views.adesao_history_json, name='history_json'),
    path('importar-pdf/', views.importar_pdf_perdcomp, name='importar_pdf'),
    path('importar-pdf-lote/', views.importar_pdf_perdcomp_lote, name='importar_pdf_lote'),
    path('importar-pedido-credito/', views.importar_pedido_credito, name='importar_pedido_credito'),
    path('importar-recibo/', views.importar_recibo_pedido_credito, name='importar_recibo'),
    path('importar-declaracao-compensacao/', views.importar_declaracao_compensacao, name='importar_declaracao_compensacao'),
    path('importar-notificacao-credito/', views.importar_notificacao_credito_conta, name='importar_credito_conta'),
    path('detectar-tipo-pdf/', views.detectar_tipo_pdf, name='detectar_tipo_pdf'),
    path('importar-lote/', views.importar_lote_page, name='importar_lote_page'),
    path('importar-logs/', views.importacao_logs_page, name='importacao_logs_page'),

    ## API endpoint for listing adesoes 
    path('api/v1/listar-adesao/', views.AdesaoListAPI.as_view(), name='api-adesao-list'),
    path('api/v1/criar-adesao/', views.AdesaoCreateAPI.as_view(), name='api-adesao-create'),
    path('api/v1/listar-adesao/<int:pk>/', views.AdesaoDetailAPI.as_view(), name='api-adesao-detail'),

    # ...existing code...
]
