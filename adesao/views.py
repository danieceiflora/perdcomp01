from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Adesao
from django.db.models import Sum
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
        qs = super().get_queryset().select_related('cliente__id_company_vinculada', 'tese_credito_id')
        perdcomp = (self.request.GET.get('perdcomp') or '').strip()
        empresa = (self.request.GET.get('empresa') or '').strip()
        if perdcomp:
            qs = qs.filter(perdcomp__icontains=perdcomp)
        if empresa:
            qs = qs.filter(cliente__id_company_vinculada_id=empresa)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Empresas disponíveis (antes de filtros por GET, mas dentro do escopo do usuário)
        base_scope = super().get_queryset().select_related('cliente__id_company_vinculada')
        empresas_raw = base_scope.values(
            'cliente__id_company_vinculada_id',
            'cliente__id_company_vinculada__nome_fantasia',
            'cliente__id_company_vinculada__razao_social'
        ).distinct()
        empresas_opcoes = []
        for e in empresas_raw:
            emp_id = e['cliente__id_company_vinculada_id']
            if emp_id is None:
                continue
            nome = e['cliente__id_company_vinculada__nome_fantasia'] or e['cliente__id_company_vinculada__razao_social']
            empresas_opcoes.append({'id': emp_id, 'nome': nome})
        empresas_opcoes.sort(key=lambda x: (x['nome'] or '').upper())
        context['empresas_opcoes'] = empresas_opcoes
        # Total de saldo restante considerando filtros aplicados
        filtered_qs = self.get_queryset()
        agg = filtered_qs.aggregate(total=Sum('saldo_atual'))
        context['saldo_restante_total'] = agg.get('total') or 0
        return context

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

class AdesaoDetailView(AdesaoClienteViewOnlyMixin, DetailView):
    model = Adesao
    template_name = 'adesao/adesao_detail.html'
    context_object_name = 'adesao'

    def get_queryset(self):
        # Usa o filtro do mixin e otimiza as relações
        return super().get_queryset().select_related('cliente__id_company_vinculada', 'tese_credito_id')

    def get(self, request, *args, **kwargs):
        pk = kwargs.get(self.pk_url_kwarg)
        # Queryset já filtrado pelo mixin
        queryset = self.get_queryset()
        try:
            self.object = queryset.get(pk=pk)
        except self.model.DoesNotExist:
            # Se o objeto existe, mas está fora do escopo, retorna 403 amigável
            if self.model.objects.filter(pk=pk).exists():
                messages.error(request, "Você não tem permissão para visualizar esta adesão.")
                from django.shortcuts import render
                return render(request, 'forbidden.html', {
                    'message': "Você não tem permissão para visualizar esta adesão."
                }, status=403)
            raise Http404(f"Adesão com ID {pk} não encontrada.")
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get(self, request, *args, **kwargs):
        pk = kwargs.get(self.pk_url_kwarg)
        queryset = self.get_queryset()
        try:
            self.object = queryset.get(pk=pk)
        except self.model.DoesNotExist:
            if self.model.objects.filter(pk=pk).exists():
                messages.error(request, "Você não tem permissão para visualizar esta adesão.")
                from django.shortcuts import render
                return render(request, 'forbidden.html', {
                    'message': "Você não tem permissão para visualizar esta adesão."
                }, status=403)
            raise Http404(f"Adesão com ID {pk} não encontrada.")
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


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

class AdesaoCreateAPI(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        serializer = AdesaoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdesaoDetailAPI(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]

    def get_object(self, pk):
        return get_object_or_404(Adesao, pk=pk)
    def get(self, request, pk):
        ser = AdesaoSerializer(self.get_object(pk))
        return Response(ser.data)
    def patch(self, request, pk):
        obj = self.get_object(pk)
        ser = AdesaoSerializer(obj, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, pk):
        obj = self.get_object(pk)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
