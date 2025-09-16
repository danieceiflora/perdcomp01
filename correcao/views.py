from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count
from django.db.models import ProtectedError
from .models import tipoTese, TeseCredito
from django.http import JsonResponse, Http404
from django.utils.dateformat import format as date_format
from django.utils.timezone import localtime
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .forms import TeseCreditoForm
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required


# Views para TeseCredito
class TeseCreditoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = TeseCredito
    template_name = 'correcao/tese_credito_list.html'
    context_object_name = 'teses_credito'
    paginate_by = 10
    permission_required = 'correcao.view_tesecredito'
    raise_exception = True
    
    def get_queryset(self):
        # Anotar quantidade de adesões para cada tese
        return TeseCredito.objects.all().annotate(adesoes_total=Count('adesoes'))

class TeseCreditoCreateView(PermissionRequiredMixin, CreateView):
    model = TeseCredito
    form_class = TeseCreditoForm
    template_name = 'correcao/tese_credito_form.html'
    success_url = reverse_lazy('correcao:tese_credito_list')
    permission_required = 'correcao.add_tesecredito'
    raise_exception = True
    
    def form_valid(self, form):
        messages.success(self.request, 'Tese de crédito cadastrada com sucesso!')
        return super().form_valid(form)

class TeseCreditoUpdateView(PermissionRequiredMixin, UpdateView):
    model = TeseCredito
    form_class = TeseCreditoForm
    template_name = 'correcao/tese_credito_form.html'
    success_url = reverse_lazy('correcao:tese_credito_list')
    permission_required = 'correcao.change_tesecredito'
    raise_exception = True
    
    def form_valid(self, form):
        messages.success(self.request, 'Tese de crédito atualizada com sucesso!')
        return super().form_valid(form)

class TeseCreditoDeleteView(PermissionRequiredMixin, DeleteView):
    model = TeseCredito
    template_name = 'correcao/tese_credito_confirm_delete.html'
    success_url = reverse_lazy('correcao:tese_credito_list')
    permission_required = 'correcao.delete_tesecredito'
    raise_exception = True
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = self.object
        referencias = obj.adesoes.all()
        ctx['has_references'] = referencias.exists()
        ctx['referencias'] = referencias
        return ctx
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, 'Tese de crédito excluída com sucesso!')
            return response
        except ProtectedError:
            messages.error(self.request, 'Não é possível excluir: há adesões vinculadas a esta tese de crédito.')
            return redirect(self.success_url)


@login_required
@require_GET
def tese_credito_history_json(request, pk):
    if not request.user.has_perm('correcao.view_tesecredito'):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    """Retorna histórico em JSON com diffs para a TeseCredito indicada."""
    try:
        tese = TeseCredito.objects.get(pk=pk)
    except TeseCredito.DoesNotExist:
        raise Http404
    manager = getattr(tese, 'history', None) or getattr(tese, 'historico', None)
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
                try:
                    val = getattr(record, fname)
                except Exception:
                    val = None
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
                    try:
                        curr_val = getattr(record, fname)
                        prev_val = getattr(prev, fname)
                    except Exception:
                        continue
                    if curr_val != prev_val:
                        manual.append({'field': fname, 'old': serialize_value(prev_val), 'new': serialize_value(curr_val)})
                if manual:
                    entry['changes'] = manual
                else:
                    entry['note'] = 'Alteração sem mudança perceptível nos campos desta tese.'
        result.append(entry)
    result.reverse()
    return JsonResponse({'object_id': tese.id, 'history': result})

@login_required
@require_GET
def tipo_tese_history_json(request, pk):
    if not request.user.has_perm('correcao.view_tipotese'):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    """Histórico JSON para tipoTese."""
    try:
        tt = tipoTese.objects.get(pk=pk)
    except tipoTese.DoesNotExist:
        raise Http404
    manager = getattr(tt, 'history', None) or getattr(tt, 'historico', None)
    if manager is None:
        return JsonResponse({'error': 'Histórico não configurado.'}, status=400)
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
                    entry['changes'].append({'field': fname, 'old': None, 'new': val})
        else:
            prev = history[idx-1]
            try:
                diff = record.diff_against(prev)
                for c in diff.changes:
                    entry['changes'].append({'field': c.field, 'old': c.old, 'new': c.new})
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
                        manual.append({'field': fname, 'old': prev_val, 'new': curr_val})
                if manual:
                    entry['changes'] = manual
                else:
                    entry['note'] = 'Alteração sem mudança perceptível.'
        result.append(entry)
    result.reverse()
    return JsonResponse({'object_id': tt.id, 'history': result})

# ================= DRF API Views ==================
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import  TipoTeseSerializer, TeseCreditoSerializer

class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (request.user.is_superuser or request.user.is_staff)

# Correcao API

# tipoTese API
class TipoTeseListAPI(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    def get(self, request):
        objs = tipoTese.objects.all()
        ser = TipoTeseSerializer(objs, many=True)
        return Response(ser.data)

class TipoTeseCreateAPI(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    def post(self, request):
        ser = TipoTeseSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

class TipoTeseDetailAPI(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    def get_object(self, pk):
        return get_object_or_404(tipoTese, pk=pk)
    def get(self, request, pk):
        ser = TipoTeseSerializer(self.get_object(pk))
        return Response(ser.data)
    def patch(self, request, pk):
        obj = self.get_object(pk)
        ser = TipoTeseSerializer(obj, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, pk):
        obj = self.get_object(pk)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# TeseCredito API
class TeseCreditoListAPI(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    def get(self, request):
        objs = TeseCredito.objects.all()
        ser = TeseCreditoSerializer(objs, many=True)
        return Response(ser.data)

class TeseCreditoCreateAPI(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    def post(self, request):
        ser = TeseCreditoSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

class TeseCreditoDetailAPI(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    def get_object(self, pk):
        return get_object_or_404(TeseCredito, pk=pk)
    def get(self, request, pk):
        ser = TeseCreditoSerializer(self.get_object(pk))
        return Response(ser.data)
    def patch(self, request, pk):
        obj = self.get_object(pk)
        ser = TeseCreditoSerializer(obj, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, pk):
        obj = self.get_object(pk)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
