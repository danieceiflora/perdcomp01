from django.urls import path
from . import views

app_name = 'lancamentos'

urlpatterns = [
    path('', views.LancamentosListView.as_view(), name='list'),
    path('<int:pk>/', views.LancamentoDetailView.as_view(), name='detail'),
    path('novo/', views.LancamentoCreateView.as_view(), name='create'),
    path('editar/<int:pk>/', views.LancamentoUpdateView.as_view(), name='update'),
    path('excluir/<int:pk>/', views.LancamentoDeleteView.as_view(), name='delete'),
    path('confirmar/<int:pk>/', views.confirmar_lancamento, name='confirmar'),
    path('estornar/<int:pk>/', views.estornar_lancamento, name='estornar'),
    path('editar-anexos/<int:pk>/', views.AnexosUpdateView.as_view(), name='editar_anexos'),
]