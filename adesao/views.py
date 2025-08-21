from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Adesao
from django.http import JsonResponse, Http404
from django.utils.dateformat import format as date_format
from django.utils.timezone import localtime
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
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

class AdesaoDetailView(LoginRequiredMixin, DetailView):
    model = Adesao
    template_name = 'adesao/adesao_detail.html'
    context_object_name = 'adesao'

    def get_queryset(self):
        base = Adesao.objects.select_related('cliente__id_company_vinculada', 'tese_credito_id')
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return base
        # Usuário comum: filtra pelas empresas acessíveis se houver profile
        if hasattr(user, 'profile'):
            try:
                profile = user.profile
                if getattr(profile, 'eh_cliente', False) and getattr(profile, 'empresa_vinculada', None):
                    return base.filter(cliente__id_company_vinculada=profile.empresa_vinculada)
                empresas = profile.get_empresas_acessiveis() if hasattr(profile, 'get_empresas_acessiveis') else []
                if empresas:
                    return base.filter(cliente__id_company_vinculada__in=empresas)
            except Exception:
                return base.none()
        return base.none()


@login_required
@require_GET
def adesao_history_json(request, pk):
    try:
        adesao = Adesao.objects.get(pk=pk)
    except Adesao.DoesNotExist:
        raise Http404
    manager = getattr(adesao, 'history', None) or getattr(adesao, 'historico', None)
    if manager is None:
        return JsonResponse({'error': 'Histórico não configurado.'}, status=400)

    def serialize_value(val):
        from django.db.models import Model
        import datetime
        if val is None:
            return None
        if isinstance(val, Model):
            return str(val)
        if isinstance(val, (datetime.datetime, datetime.date, datetime.time)):
            try:
                return val.isoformat()
            except Exception:
                return str(val)
        return val

    history = list(manager.all().order_by('history_date'))
    result = []
    for idx, record in enumerate(history):
        entry = {
            'id': record.id,
            'history_id': getattr(record, 'history_id', None),
            'history_date': date_format(localtime(record.history_date), 'd/m/Y H:i:s'),
            'history_user': getattr(record.history_user, 'username', None),
            'history_type': record.history_type,
            'changes': [],
            'note': ''
        }
        if idx == 0:
            for field in record._meta.fields:
                fname = field.name
                if fname in ('history_id','history_date','history_change_reason','history_type','history_user','id'):
                    continue
                val = getattr(record, fname, None)
                if val not in (None, ''):
                    entry['changes'].append({'field': fname, 'old': None, 'new': serialize_value(val)})
        else:
            prev = history[idx-1]
            try:
                diff = record.diff_against(prev)
                for c in diff.changes:
                    entry['changes'].append({'field': c.field, 'old': serialize_value(c.old), 'new': serialize_value(c.new)})
            except Exception:
                pass
            if not entry['changes']:
                ignore = {'history_id','history_date','history_change_reason','history_type','history_user','id'}
                manual = []
                for field in record._meta.fields:
                    fname = field.name
                    if fname in ignore:
                        continue
                    curr_val = getattr(record, fname, None)
                    prev_val = getattr(prev, fname, None)
                    if curr_val != prev_val:
                        manual.append({'field': fname, 'old': serialize_value(prev_val), 'new': serialize_value(curr_val)})
                if manual:
                    entry['changes'] = manual
                else:
                    entry['note'] = 'Alteração sem mudança perceptível.'
        result.append(entry)
    result.reverse()
    return JsonResponse({'object_id': adesao.id, 'history': result})


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

