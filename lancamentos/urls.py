from django.urls import path
from . import views

app_name = 'lancamentos'

urlpatterns = [
    path('', views.LancamentosListView.as_view(), name='list'),
    path('<int:pk>/', views.LancamentoDetailView.as_view(), name='detail'),
    path('novo/', views.LancamentoCreateView.as_view(), name='create'),
    path('editar-anexos/<int:pk>/', views.AnexosUpdateView.as_view(), name='editar_anexos'),
    path('criar-estorno/<int:pk>/', views.criar_estorno, name='criar_estorno'),
]