
from django.urls import path
from . import views

app_name = 'lancamentos'

urlpatterns = [
    path('', views.LancamentosListView.as_view(), name='list'),
    path('<int:pk>/', views.LancamentoDetailView.as_view(), name='detail'),
    path('novo/', views.LancamentoCreateView.as_view(), name='create'),
    path('exportar-xlsx/', views.exportar_lancamentos_xlsx, name='exportar_xlsx'),
    path('historico/<int:pk>/', views.lancamento_history_json, name='history_json'),
    path('historico-anexo/<int:pk>/', views.anexo_history_json, name='anexo_history_json'),
    ##path('editar-anexos/<int:pk>/', views.AnexosUpdateView.as_view(), name='editar_anexos')
]