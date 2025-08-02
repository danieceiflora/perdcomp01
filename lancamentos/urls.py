
from django.urls import path
from . import views

app_name = 'lancamentos'

urlpatterns = [
    path('', views.LancamentosListView.as_view(), name='list'),
    path('<int:pk>/', views.LancamentoDetailView.as_view(), name='detail'),
    path('novo/', views.LancamentoCreateView.as_view(), name='create'),
    path('exportar-xlsx/', views.exportar_lancamentos_xlsx, name='exportar_xlsx'),
    ##path('editar-anexos/<int:pk>/', views.AnexosUpdateView.as_view(), name='editar_anexos')
]