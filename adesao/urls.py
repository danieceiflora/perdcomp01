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
    path('api/v1/listar-adesoes/', views.AdesaoListAPI.as_view(), name='api-list'),
    path('api/v1/create/', views.AdesaoCreateApi.as_view(), name='api-create'),

    ## listar adesão por id
    path('api/v1/<int:pk>/', views.AdesaoDetailApi.as_view(), name='api-detail'),

    # ...existing code...
]
