from django.urls import path
from . import views

app_name = 'correcao'

urlpatterns = [
    path('', views.CorrecaoListView.as_view(), name='list'),
    path('novo/', views.CorrecaoCreateView.as_view(), name='create'),
    path('editar/<int:pk>/', views.CorrecaoUpdateView.as_view(), name='update'),
    path('excluir/<int:pk>/', views.CorrecaoDeleteView.as_view(), name='delete'),
]
