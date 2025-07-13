from django.urls import path
from . import views

app_name = 'adesao'

urlpatterns = [
    path('', views.AdesaoListView.as_view(), name='list'),
    path('novo/', views.AdesaoCreateView.as_view(), name='create'),
    path('editar/<int:pk>/', views.AdesaoUpdateView.as_view(), name='update'),
    path('excluir/<int:pk>/', views.AdesaoDeleteView.as_view(), name='delete'),
]
