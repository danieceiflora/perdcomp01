
from django.urls import path
from . import views

app_name = 'lancamentos'

urlpatterns = [
    path('', views.LancamentosListView.as_view(), name='list'),
    path('<int:pk>/', views.LancamentoDetailView.as_view(), name='detail'),
    path('<int:pk>/aprovar/', views.LancamentoApprovalUpdateView.as_view(), name='aprovar'),
    path('novo/', views.LancamentoCreateView.as_view(), name='create'),
    path('exportar-xlsx/', views.exportar_lancamentos_xlsx, name='exportar_xlsx'),
    path('historico/<int:pk>/', views.lancamento_history_json, name='history_json'),
    path('historico-anexo/<int:pk>/', views.anexo_history_json, name='anexo_history_json'),
    path('importar-recibo/', views.importar_recibo_lancamento, name='importar_recibo'),
    ##path('editar-anexos/<int:pk>/', views.AnexosUpdateView.as_view(), name='editar_anexos')
    # API DRF padronizada
    path('api/v1/listar-lancamento/', views.LancamentoListAPI.as_view(), name='api-lancamento-list'),
    path('api/v1/criar-lancamento/', views.LancamentoCreateAPI.as_view(), name='api-lancamento-create'),
    path('api/v1/listar-lancamento/<int:pk>/', views.LancamentoDetailAPI.as_view(), name='api-lancamento-detail'),
    path('api/v1/listar-anexo/', views.AnexoListAPI.as_view(), name='api-anexo-list'),
    path('api/v1/criar-anexo/', views.AnexoCreateAPI.as_view(), name='api-anexo-create'),
    path('api/v1/listar-anexo/<int:pk>/', views.AnexoDetailAPI.as_view(), name='api-anexo-detail'),
]