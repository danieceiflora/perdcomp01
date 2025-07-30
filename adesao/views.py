from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Adesao
from .forms import AdesaoForm
from .permissions import AdesaoPermissionMixin, AdesaoClienteViewOnlyMixin, AdminRequiredMixin

# Adicionando imports do DRF
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import AdesaoSerializer

# Permissão customizada para superadmin
class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser

class AdesaoListView(AdesaoClienteViewOnlyMixin, ListView):
    model = Adesao
    template_name = 'adesao/adesao_list.html'
    context_object_name = 'adesoes'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('cliente__id_company_vinculada', 'tese_credito_id')
        return queryset

class AdesaoCreateView(AdminRequiredMixin, CreateView):
    model = Adesao
    form_class = AdesaoForm
    template_name = 'adesao/adesao_form.html'
    success_url = reverse_lazy('adesao:list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Adesão cadastrada com sucesso!')
        return super().form_valid(form)

class AdesaoUpdateView(AdminRequiredMixin, UpdateView):
    model = Adesao
    form_class = AdesaoForm
    template_name = 'adesao/adesao_form.html'
    success_url = reverse_lazy('adesao:list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Adesão atualizada com sucesso!')
        return super().form_valid(form)


class AdesaoListAPI(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        adesoes = Adesao.objects.all()
        serializer = AdesaoSerializer(adesoes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AdesaoCreateApi(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        serializer = AdesaoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

