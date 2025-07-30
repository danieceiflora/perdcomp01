from django.urls import path
from . import views


app_name = 'adesao'

urlpatterns = [
    path('', views.AdesaoListView.as_view(), name='list'),
    path('novo/', views.AdesaoCreateView.as_view(), name='create'),
    path('editar/<int:pk>/', views.AdesaoUpdateView.as_view(), name='update'),

    ## API endpoint for listing adesoes 
    path('api/listar-adesoes/', views.AdesaoListAPI.as_view(), name='api-list'),
    path('api/adesao/create/', views.AdesaoCreateApi.as_view(), name='api-create'),

    # ...existing code...
]
