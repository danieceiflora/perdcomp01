from django.urls import path
from . import views


app_name = 'adesao'

urlpatterns = [
    path('', views.AdesaoListView.as_view(), name='list'),
    path('novo/', views.AdesaoCreateView.as_view(), name='create'),
    path('editar/<int:pk>/', views.AdesaoUpdateView.as_view(), name='update'),
    path('detalhe/<int:pk>/', views.AdesaoDetailView.as_view(), name='detail'),
    path('historico/<int:pk>/', views.adesao_history_json, name='history_json'),

    ## API endpoint for listing adesoes 
    path('api/v1/listar-adesao/', views.AdesaoListAPI.as_view(), name='api-adesao-list'),
    path('api/v1/criar-adesao/', views.AdesaoCreateAPI.as_view(), name='api-adesao-create'),
    path('api/v1/listar-adesao/<int:pk>/', views.AdesaoDetailAPI.as_view(), name='api-adesao-detail'),

    # ...existing code...
]
