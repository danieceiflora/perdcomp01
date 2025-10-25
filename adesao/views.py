from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Adesao
from lancamentos.models import Lancamentos
from django.db import transaction
from django.http import HttpResponseRedirect
from django.db.models import Sum
from django.http import JsonResponse, Http404
from django.utils.dateformat import format as date_format
from django.utils.timezone import localtime
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from .forms import AdesaoForm
from django.views.decorators.http import require_POST
import re
from typing import Any
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie, csrf_protect
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone
from utils.pdf_parser import parse_ressarcimento_text, parse_recibo_pedido_credito_text, parse_credito_em_conta_text
from pdf import extract_text
from clientes_parceiros.models import ClientesParceiros
from .permissions import AdesaoPermissionMixin, AdesaoClienteViewOnlyMixin, AdminRequiredMixin
from datetime import datetime

# Adicionando imports do DRF
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import AdesaoSerializer

# Permissão customizada para superadmin
class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser

from django.utils.decorators import method_decorator

@method_decorator(ensure_csrf_cookie, name='dispatch')
class AdesaoListView(AdesaoClienteViewOnlyMixin, ListView):
    model = Adesao
    template_name = 'adesao/adesao_list.html'
    context_object_name = 'adesoes'
    paginate_by = 10
    
    def get_queryset(self):
        qs = super().get_queryset().select_related('cliente__id_company_vinculada')
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
        # Validação extra: quando método = Escriturial, exigir origem e data_origem
        metodo = form.cleaned_data.get('metodo_credito')
        if metodo == 'Escritural':
            origem = form.cleaned_data.get('origem')
            data_origem = form.cleaned_data.get('data_origem')
            if not origem:
                form.add_error('origem', 'Informe a Origem (escritural).')
            if not data_origem:
                form.add_error('data_origem', 'Informe a Data de Origem (escritural).')
            if form.errors:
                return self.form_invalid(form)

        # Processamento de débitos vinculados a tipos específicos (multi-itens)
        requires_debitos = metodo in (
            'Compensação vinculada a um pedido de ressarcimento',
            'Compensação vinculada a um pedido de restituição',
        )

        # Captura débitos do POST (antes de salvar)
        total_forms = int(self.request.POST.get('debitos-TOTAL_FORMS') or 0)
        debitos = []
        for i in range(total_forms):
            cod_denom = (self.request.POST.get(f'debitos-{i}-codigo_receita_denominacao') or '').strip()
            per_ap = (self.request.POST.get(f'debitos-{i}-periodo_apuracao_debito') or '').strip()
            val = (self.request.POST.get(f'debitos-{i}-total') or '').strip()
            if not cod_denom and not per_ap and not val:
                continue
            try:
                valor = float(val.replace(',', '.')) if val else None
            except ValueError:
                valor = None
            debitos.append({
                'codigo_receita_denominacao': cod_denom,
                'periodo_apuracao_debito': per_ap,
                'valor': valor,
            })

        # Validação de quantidade para tipos que exigem ao menos um débito
        if requires_debitos and not debitos:
            messages.error(self.request, 'Inclua pelo menos um débito vinculado para este tipo de crédito.')
            return self.form_invalid(form)
        # Salva a adesão e cria os débitos de forma atômica
        from django.utils import timezone as dj_tz
        try:
            with transaction.atomic():
                self.object = form.save()
                adesao: Adesao = self.object
                for d in debitos:
                    if d.get('valor') in (None, ''):
                        continue
                    Lancamentos.objects.create(
                        id_adesao=adesao,
                        data_lancamento=dj_tz.now(),
                        valor=d['valor'],
                        sinal='-',
                        tipo='Gerado',
                        descricao='Débito vinculado ao crédito (PERDCOMP) informado na adesão',
                        metodo=metodo,
                        codigo_receita_denominacao=d.get('codigo_receita_denominacao') or None,
                        periodo_apuracao_debito=d.get('periodo_apuracao_debito') or None,
                        aprovado=True,
                    )
        except Exception as e:
            # Define erro no formulário para exibir feedback
            form.add_error(None, f"Falha ao salvar débitos vinculados: {e}")
            return self.form_invalid(form)

        messages.success(self.request, 'Adesão cadastrada com sucesso!')
        return HttpResponseRedirect(self.get_success_url())

class AdesaoUpdateView(AdminRequiredMixin, UpdateView):
    model = Adesao
    form_class = AdesaoForm
    template_name = 'adesao/adesao_form.html'
    success_url = reverse_lazy('adesao:list')
    
    def form_valid(self, form):
        metodo = form.cleaned_data.get('metodo_credito')
        if metodo == 'Escritural':
            origem = form.cleaned_data.get('origem')
            data_origem = form.cleaned_data.get('data_origem')
            if not origem:
                form.add_error('origem', 'Informe a Origem (escritural).')
            if not data_origem:
                form.add_error('data_origem', 'Informe a Data de Origem (escritural).')
            if form.errors:
                return self.form_invalid(form)

        # Capturar possíveis novos débitos informados no update e criar lançamentos adicionais
        total_forms = int(self.request.POST.get('debitos-TOTAL_FORMS') or 0)
        debitos = []
        for i in range(total_forms):
            cod_denom = (self.request.POST.get(f'debitos-{i}-codigo_receita_denominacao') or '').strip()
            per_ap = (self.request.POST.get(f'debitos-{i}-periodo_apuracao_debito') or '').strip()
            val = (self.request.POST.get(f'debitos-{i}-total') or '').strip()
            if not cod_denom and not per_ap and not val:
                continue
            try:
                valor = float(val.replace(',', '.')) if val else None
            except ValueError:
                valor = None
            debitos.append({
                'codigo_receita_denominacao': cod_denom,
                'periodo_apuracao_debito': per_ap,
                'valor': valor,
            })

        from django.utils import timezone as dj_tz
        try:
            with transaction.atomic():
                response = super().form_valid(form)
                adesao: Adesao = self.object
                for d in debitos:
                    if d.get('valor') in (None, ''):
                        continue
                    Lancamentos.objects.create(
                        id_adesao=adesao,
                        data_lancamento=dj_tz.now(),
                        valor=d['valor'],
                        sinal='-',
                        tipo='Gerado',
                        descricao='Débito vinculado ao crédito (PERDCOMP) informado na adesão',
                        metodo=metodo,
                        codigo_receita_denominacao=d.get('codigo_receita_denominacao') or None,
                        periodo_apuracao_debito=d.get('periodo_apuracao_debito') or None,
                        aprovado=True,
                    )
        except Exception as e:
            form.add_error(None, f"Falha ao salvar débitos vinculados no update: {e}")
            return self.form_invalid(form)

        messages.success(self.request, 'Adesão atualizada com sucesso!')
        return response

class AdesaoDetailView(AdesaoClienteViewOnlyMixin, DetailView):
    model = Adesao
    template_name = 'adesao/adesao_detail.html'
    context_object_name = 'adesao'

    def get_queryset(self):
        # Usa o filtro do mixin e otimiza as relações
        return super().get_queryset().select_related('cliente__id_company_vinculada')

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


@login_required
@csrf_protect
@require_POST
def importar_pdf_perdcomp(request):
    """Recebe um PDF, extrai texto, faz parsing e validações. Retorna JSON.
    Valida: cliente por CNPJ; unicidade de PERDCOMP.
    """
    pdf_file: UploadedFile | None = request.FILES.get('pdf')
    if not pdf_file:
        return JsonResponse({'ok': False, 'error': 'Arquivo PDF não enviado (campo "pdf").'}, status=400)

    # Armazena temporário em memória/arquivo
    import tempfile
    import os
    log_data = {
        'user': getattr(request.user, 'username', None),
        'filename': pdf_file.name,
        'ts': timezone.now().isoformat(),
    }
    status_code = 200
    response_payload = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            for chunk in pdf_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        txt = extract_text(tmp_path) or ''
        parsed = parse_ressarcimento_text(txt)

        log_data['extracted_present'] = bool(txt)
        log_data['parsed'] = parsed.as_dict()

        # Validar CNPJ -> cliente
        cnpj = parsed.cnpj or ''
        cliente_id = None
        cliente_label = None
        if cnpj:
            try:
                cliente = ClientesParceiros.objects.select_related('id_company_vinculada').get(
                    id_company_vinculada__cnpj=cnpj
                )
                cliente_id = cliente.id
                emp = cliente.id_company_vinculada
                cliente_label = f"{emp.nome_fantasia or emp.razao_social} ({cliente.nome_referencia})"
            except ClientesParceiros.DoesNotExist:
                status_code = 404
                response_payload = {'ok': False, 'error': f'Cliente com CNPJ {cnpj} não encontrado.'}
        else:
            status_code = 400
            response_payload = {'ok': False, 'error': 'CNPJ não identificado no PDF.'}

        # Validar PERDCOMP presente
        if status_code == 200 and not parsed.perdcomp:
            status_code = 400
            response_payload = {'ok': False, 'error': 'Declaração PERDCOMP não identificada no PDF.'}

        # Validar PERDCOMP único
        if status_code == 200 and parsed.perdcomp and Adesao.objects.filter(perdcomp=parsed.perdcomp).exists():
            status_code = 409
            response_payload = {'ok': False, 'error': f'PERDCOMP {parsed.perdcomp} já cadastrado.'}

        if status_code == 200:
            criar = str(request.POST.get('criar', '0')).lower() in ('1','true','on','yes')
            metodo_credito_val = (parsed.metodo_credito or '').strip()
            metodo_credito_lower = metodo_credito_val.lower()
            comp_vinc = any(
                keyword in metodo_credito_lower for keyword in (
                    'compensação vinculada a um pedido de ressarcimento',
                    'compensação vinculada a um pedido de restituição',
                    'pedido de ressarcimento',
                    'pedido de restituição',
                )
            )
            if criar and comp_vinc and cliente_id:
                # Criar Adesão + Lançamentos (débitos) seguindo lógica do lançamento manual
                from decimal import Decimal
                from django.db import transaction
                # saldo base: valor do pedido se existir, senão soma dos débitos
                soma_debitos = Decimal('0')
                for d in (parsed.debitos or []):
                    v = d.get('valor')
                    if v is not None:
                        try:
                            soma_debitos += Decimal(str(v))
                        except Exception:
                            pass
                # Regra unificada: usar "Valor Original do Crédito Inicial" para saldo base
                saldo_base = getattr(parsed, 'valor_original_credito_inicial', None)
                if saldo_base is None:
                    saldo_base = parsed.valor_pedido if parsed.valor_pedido is not None else soma_debitos
                # helper de data
                def _conv_date(dmy: str) -> str | None:
                    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", dmy or '')
                    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None
                try:
                    with transaction.atomic():
                        cliente_obj = ClientesParceiros.objects.get(id=cliente_id)
                        ad = Adesao.objects.create(
                            cliente=cliente_obj,
                            perdcomp=parsed.perdcomp or '',
                            metodo_credito=metodo_credito_val or None,
                            data_inicio=_conv_date(parsed.data_criacao) or timezone.now().date(),
                            saldo=float(saldo_base or 0),
                            ano=parsed.ano or None,
                            trimestre=parsed.trimestre or None,
                            tipo_credito=(parsed.tipo_credito or '')[:200] or None,
                            periodo_apuracao_credito=parsed.periodo_apuracao_credito or None,
                            codigo_receita=(parsed.codigo_receita or '')[:100] or None,
                        )
                        from django.utils import timezone as dj_tz
                        for d in (parsed.debitos or []):
                            val = d.get('valor')
                            if val is None:
                                continue
                            Lancamentos.objects.create(
                                id_adesao=ad,
                                data_lancamento=dj_tz.now(),
                                valor=float(val),
                                sinal='-',
                                tipo='Gerado',
                                descricao='Débito vinculado (importado do PDF) - Declaração de Compensação',
                                metodo=parsed.metodo_credito,
                                codigo_receita_denominacao=(d.get('codigo_receita_denominacao') or None),
                                periodo_apuracao_debito=(d.get('periodo_apuracao_debito') or None),
                                aprovado=True,
                            )
                    response_payload = {
                        'ok': True,
                        'created': True,
                        'id': ad.pk,
                        'detail_url': reverse('adesao:detail', kwargs={'pk': ad.pk}),
                    }
                except Exception as e:
                    status_code = 400
                    response_payload = {'ok': False, 'error': f'Falha ao criar adesão e débitos: {e}'}
            else:
                response_payload = {
                    'ok': True,
                    'fields': {
                        'cliente': {'id': cliente_id, 'label': cliente_label},
                        'perdcomp': parsed.perdcomp,
                        'metodo_credito': parsed.metodo_credito,
                        'data_inicio': parsed.data_criacao,  # poderá ser ajustado no frontend
                        'valor_do_credito': str(parsed.valor_pedido) if parsed.valor_pedido is not None else None,
                        'valor_total_origem': str(parsed.valor_total_origem) if getattr(parsed, 'valor_total_origem', None) is not None else None,
                        'valor_original_credito_inicial': str(getattr(parsed, 'valor_original_credito_inicial', None)) if getattr(parsed, 'valor_original_credito_inicial', None) is not None else None,
                        'ano': parsed.ano,
                        'trimestre': parsed.trimestre,
                        'tipo_credito': parsed.tipo_credito,
                        # Novos campos para Pedido de restituição
                        'data_arrecadacao': parsed.data_arrecadacao,
                        'periodo_apuracao_credito': parsed.periodo_apuracao_credito,
                        'codigo_receita': parsed.codigo_receita,
                        'debitos': [
                            {
                                'codigo_receita_denominacao': d.get('codigo_receita_denominacao'),
                                'periodo_apuracao_debito': d.get('periodo_apuracao_debito'),
                                'valor': str(d.get('valor')) if d.get('valor') is not None else None,
                            }
                            for d in (parsed.debitos or [])
                        ],
                    }
                }
    except Exception as e:
        status_code = 500
        response_payload = {'ok': False, 'error': f'Erro ao processar PDF: {str(e)}'}
    finally:
        # Attach result metadata for logging purposes
        final_payload = response_payload or {'ok': False, 'error': 'Falha ao processar PDF.'}
        log_data['result'] = final_payload
        log_data['status_code'] = status_code
        
        # Audit log simples por arquivo
        try:
            from django.conf import settings
            import json
            logs_dir = os.path.join(getattr(settings, 'MEDIA_ROOT', ''), 'import_logs')
            os.makedirs(logs_dir, exist_ok=True)
            safe_name = os.path.basename(pdf_file.name).replace(' ', '_')
            log_path = os.path.join(logs_dir, f"import_{timezone.now().strftime('%Y%m%d_%H%M%S')}_{safe_name}.json")
            import json
            json_payload = json.dumps(log_data, ensure_ascii=False, indent=2)
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(json_payload)
        except Exception:
            pass
        try:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

    return JsonResponse(final_payload, status=status_code)


@login_required
@csrf_protect
@require_POST
def importar_recibo_pedido_credito(request):
    pdf_file: UploadedFile | None = request.FILES.get('pdf')
    if not pdf_file:
        return JsonResponse({'ok': False, 'error': 'Arquivo PDF não enviado (campo "pdf").'}, status=400)

    import tempfile
    import os
    from django.conf import settings
    status_code = 200
    response_payload: dict[str, Any] | None = None
    log_data: dict[str, Any] = {
        'user': getattr(request.user, 'username', None),
        'filename': pdf_file.name,
        'ts': timezone.now().isoformat(),
        'context': 'recibo_pedido_credito',
    }

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            for chunk in pdf_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        txt = extract_text(tmp_path) or ''
        parsed = parse_recibo_pedido_credito_text(txt)
        log_data['parsed'] = parsed.as_dict()

        numero_documento = (parsed.numero_documento or '').strip()
        if not numero_documento:
            status_code = 400
            response_payload = {'ok': False, 'error': 'Número do Documento não identificado no PDF.'}
        else:
            try:
                adesao = Adesao.objects.get(perdcomp=numero_documento)
            except Adesao.DoesNotExist:
                status_code = 404
                response_payload = {'ok': False, 'error': f'Adesão com PERDCOMP {numero_documento} não encontrada.'}

        if status_code == 200:
            missing = []
            numero_controle = (parsed.numero_controle or '').strip()
            if not numero_controle:
                missing.append('Número de Controle')
            autenticacao_serpro = (parsed.autenticacao_serpro or '').strip()
            if not autenticacao_serpro:
                missing.append('Autenticação SERPRO')
            if missing:
                status_code = 400
                response_payload = {'ok': False, 'error': f'Campo(s) não identificado(s) no PDF: {", ".join(missing)}.'}

        if status_code == 200:
            fields_to_update = []
            if numero_controle:
                adesao.numero_controle = numero_controle
                fields_to_update.append('numero_controle')
            if autenticacao_serpro:
                adesao.chave_seguranca_serpro = autenticacao_serpro
                fields_to_update.append('chave_seguranca_serpro')

            adesao.status = 'protocolado'
            fields_to_update.append('status')
            adesao.save(update_fields=fields_to_update)

            response_payload = {
                'ok': True,
                'id': adesao.pk,
                'detail_url': reverse('adesao:detail', kwargs={'pk': adesao.pk}),
                'numero_controle': adesao.numero_controle,
                'chave_seguranca_serpro': adesao.chave_seguranca_serpro,
                'status': adesao.get_status_display(),
                'numero_documento': numero_documento,
            }

    except Exception as e:
        status_code = 500
        response_payload = {'ok': False, 'error': f'Erro ao processar PDF: {str(e)}'}
    finally:
        try:
            log_data['status_code'] = status_code
            log_data['result'] = response_payload
            logs_dir = os.path.join(getattr(settings, 'MEDIA_ROOT', ''), 'import_logs')
            os.makedirs(logs_dir, exist_ok=True)
            safe_name = os.path.basename(pdf_file.name).replace(' ', '_')
            log_path = os.path.join(
                logs_dir,
                f"recibo_{timezone.now().strftime('%Y%m%d_%H%M%S')}_{safe_name}.json"
            )
            import json
            with open(log_path, 'w', encoding='utf-8') as fh:
                fh.write(json.dumps(log_data, ensure_ascii=False, indent=2))
        except Exception:
            pass
        try:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

    return JsonResponse(response_payload or {'ok': False, 'error': 'Falha desconhecida.'}, status=status_code)


@login_required
@csrf_protect
@require_POST
def importar_notificacao_credito_conta(request):
    pdf_file: UploadedFile | None = request.FILES.get('pdf')
    if not pdf_file:
        return JsonResponse({'ok': False, 'error': 'Arquivo PDF não enviado (campo "pdf").'}, status=400)

    import tempfile
    import os
    from django.conf import settings

    status_code = 200
    response_payload: dict[str, Any] | None = None
    log_data: dict[str, Any] = {
        'user': getattr(request.user, 'username', None),
        'filename': pdf_file.name,
        'ts': timezone.now().isoformat(),
        'context': 'credito_em_conta',
    }

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            for chunk in pdf_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        txt = extract_text(tmp_path) or ''
        parsed = parse_credito_em_conta_text(txt)
        log_data['parsed'] = parsed.as_dict()

        perdcomp = (parsed.perdcomp or '').strip()
        data_credito_str = (parsed.data_credito or '').strip()
        valor_credito = parsed.valor_credito

        if not perdcomp:
            status_code = 400
            response_payload = {'ok': False, 'error': 'PERDCOMP não identificado na notificação.'}
        else:
            try:
                adesao = Adesao.objects.get(perdcomp=perdcomp)
            except Adesao.DoesNotExist:
                status_code = 404
                response_payload = {'ok': False, 'error': f'Adesão com PERDCOMP {perdcomp} não encontrada.'}

        if status_code == 200 and not data_credito_str:
            status_code = 400
            response_payload = {'ok': False, 'error': 'Data do crédito não identificada no PDF.'}

        if status_code == 200 and valor_credito is None:
            status_code = 400
            response_payload = {'ok': False, 'error': 'Valor creditado não identificado no PDF.'}

        if status_code == 200:
            try:
                data_credito = datetime.strptime(data_credito_str, '%d/%m/%Y').date()
            except ValueError:
                status_code = 400
                response_payload = {'ok': False, 'error': f'Data do crédito inválida: {data_credito_str}'}
            else:
                try:
                    valor_float = float(valor_credito)
                except (TypeError, ValueError):
                    status_code = 400
                    response_payload = {'ok': False, 'error': 'Valor creditado inválido.'}
                else:
                    if valor_float <= 0:
                        status_code = 400
                        response_payload = {'ok': False, 'error': 'Valor creditado deve ser maior que zero.'}

        if status_code == 200:
            exists = Lancamentos.objects.filter(
                id_adesao=adesao,
                metodo='Crédito em conta',
                data_credito=data_credito,
                valor_credito_em_conta=valor_float
            ).exists()
            if exists:
                status_code = 409
                response_payload = {'ok': False, 'error': 'Notificação já importada anteriormente para esta adesão.'}

        if status_code == 200:
            credit_datetime = datetime.combine(data_credito, datetime.min.time().replace(hour=12, minute=0))
            if timezone.is_naive(credit_datetime):
                credit_datetime = timezone.make_aware(credit_datetime, timezone.get_current_timezone())

            lancamento = Lancamentos.objects.create(
                id_adesao=adesao,
                data_lancamento=credit_datetime,
                valor=valor_float,
                sinal='+',
                tipo='Gerado',
                descricao='Crédito em conta importado automaticamente.',
                metodo='Crédito em conta',
                data_credito=data_credito,
                valor_credito_em_conta=valor_float,
                aprovado=True,
                observacao_aprovacao='Importação automática via notificação de crédito em conta.'
            )

            adesao.refresh_from_db(fields=['saldo_atual'])

            fields_to_update: list[str] = []
            if adesao.data_credito_em_conta != data_credito:
                adesao.data_credito_em_conta = data_credito
                fields_to_update.append('data_credito_em_conta')
            if adesao.valor_credito_em_conta != valor_float:
                adesao.valor_credito_em_conta = valor_float
                fields_to_update.append('valor_credito_em_conta')
            if adesao.status != 'protocolado':
                adesao.status = 'protocolado'
                fields_to_update.append('status')
            if fields_to_update:
                adesao.save(update_fields=fields_to_update)

            response_payload = {
                'ok': True,
                'perdcomp': adesao.perdcomp,
                'lancamento_id': lancamento.pk,
                'lancamento_detail_url': reverse('lancamentos:detail', kwargs={'pk': lancamento.pk}),
                'saldo_atual': adesao.saldo_atual,
                'valor_creditado': valor_float,
                'data_credito': data_credito.strftime('%d/%m/%Y'),
            }

    except Exception as e:
        status_code = 500
        response_payload = {'ok': False, 'error': f'Erro ao processar PDF: {str(e)}'}
    finally:
        try:
            log_data['status_code'] = status_code
            log_data['result'] = response_payload
            logs_dir = os.path.join(getattr(settings, 'MEDIA_ROOT', ''), 'import_logs')
            os.makedirs(logs_dir, exist_ok=True)
            safe_name = os.path.basename(pdf_file.name).replace(' ', '_')
            log_path = os.path.join(
                logs_dir,
                f"credito_conta_{timezone.now().strftime('%Y%m%d_%H%M%S')}_{safe_name}.json"
            )
            import json
            with open(log_path, 'w', encoding='utf-8') as fh:
                fh.write(json.dumps(log_data, ensure_ascii=False, indent=2))
        except Exception:
            pass
        try:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

    return JsonResponse(response_payload or {'ok': False, 'error': 'Falha desconhecida.'}, status=status_code)


@login_required
@require_POST
def importar_pdf_perdcomp_lote(request):
    """Importação em lote de PDFs PERDCOMP.
    Campo de arquivos: 'pdfs' (múltiplos). Se 'criar' for truthy, criará as Adesões automaticamente.
    Retorna JSON com a lista de resultados por arquivo (ok/error, mensagens e link quando criado).
    """
    if not (request.user.is_superuser or request.user.is_staff or request.user.has_perm('adesao.add_adesao')):
        return JsonResponse({'ok': False, 'error': 'Permissão negada para importar adesões.'}, status=403)
    files = request.FILES.getlist('pdfs') or request.FILES.getlist('pdf')
    criar = str(request.POST.get('criar', '0')).lower() in ('1', 'true', 'on', 'yes')
    if not files:
        return JsonResponse({'ok': False, 'error': 'Nenhum arquivo PDF enviado.'}, status=400)

    import tempfile, os, datetime, re
    from django.conf import settings
    from django.urls import reverse
    results = []

    def write_log(base_filename: str, payload: dict):
        try:
            logs_dir = os.path.join(getattr(settings, 'MEDIA_ROOT', ''), 'import_logs')
            os.makedirs(logs_dir, exist_ok=True)
            ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            safe_name = os.path.basename(base_filename).replace(' ', '_')
            path = os.path.join(logs_dir, f"batch_{ts}_{safe_name}.json")
            import json
            json_payload = json.dumps(payload, ensure_ascii=False, indent=2)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(json_payload)
        except Exception:
            pass

    for f in files:
        context_log = {
            'user': getattr(request.user, 'username', None),
            'filename': f.name,
        }
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                for chunk in f.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name

            txt = extract_text(tmp_path) or ''
            parsed = parse_ressarcimento_text(txt)
            context_log['extracted_present'] = bool(txt)
            context_log['parsed'] = parsed.as_dict()

            # Validar CNPJ
            cnpj = parsed.cnpj or ''
            if not cnpj:
                msg = 'CNPJ não identificado no PDF.'
                res = {'file': f.name, 'ok': False, 'error': msg}
                results.append(res)
                context_log['result'] = res
                write_log(f.name, context_log)
                continue
            try:
                cliente = ClientesParceiros.objects.select_related('id_company_vinculada').get(
                    id_company_vinculada__cnpj=cnpj
                )
            except ClientesParceiros.DoesNotExist:
                msg = f'Cliente com CNPJ {cnpj} não encontrado.'
                res = {'file': f.name, 'ok': False, 'error': msg}
                results.append(res)
                context_log['result'] = res
                write_log(f.name, context_log)
                continue

            # Validar PERDCOMP
            if not parsed.perdcomp:
                msg = 'PERDCOMP não identificado no PDF.'
                res = {'file': f.name, 'ok': False, 'error': msg}
                results.append(res)
                context_log['result'] = res
                write_log(f.name, context_log)
                continue
            if Adesao.objects.filter(perdcomp=parsed.perdcomp).exists():
                msg = f'PERDCOMP {parsed.perdcomp} já cadastrado.'
                res = {'file': f.name, 'ok': False, 'error': msg}
                results.append(res)
                context_log['result'] = res
                write_log(f.name, context_log)
                continue

            # Apenas extrair (sem criar)
            if not criar:
                emp = cliente.id_company_vinculada
                cliente_label = f"{emp.nome_fantasia or emp.razao_social} ({cliente.nome_referencia})"
                res = {
                    'file': f.name,
                    'ok': True,
                    'created': False,
                    'fields': {
                        'cliente': cliente.id,
                        'cliente_label': cliente_label,
                        'perdcomp': parsed.perdcomp,
                        'metodo_credito': parsed.metodo_credito,
                        'data_inicio': parsed.data_criacao,
                        'saldo': str(parsed.valor_pedido) if parsed.valor_pedido is not None else None,
                        'valor_total_origem': str(getattr(parsed, 'valor_total_origem', None)) if getattr(parsed, 'valor_total_origem', None) is not None else None,
                        'valor_original_credito_inicial': str(getattr(parsed, 'valor_original_credito_inicial', None)) if getattr(parsed, 'valor_original_credito_inicial', None) is not None else None,
                        'ano': parsed.ano,
                        'trimestre': parsed.trimestre,
                        'tipo_credito': parsed.tipo_credito,
                        'data_arrecadacao': parsed.data_arrecadacao,
                        'periodo_apuracao_credito': parsed.periodo_apuracao_credito,
                        'codigo_receita': parsed.codigo_receita,
                        'debitos': [
                            {
                                'codigo_receita_denominacao': d.get('codigo_receita_denominacao'),
                                'periodo_apuracao_debito': d.get('periodo_apuracao_debito'),
                                'valor': str(d.get('valor')) if d.get('valor') is not None else None,
                            }
                            for d in (parsed.debitos or [])
                        ],
                    }
                }
                results.append(res)
                context_log['result'] = res
                write_log(f.name, context_log)
                continue

            # Criar registro(s)
            comp_vinc = parsed.metodo_credito in (
                'Compensação vinculada a um pedido de ressarcimento',
                'Compensação vinculada a um pedido de restituição',
            )
            def _conv_date(dmy: str) -> str | None:
                m = re.match(r"(\d{2})/(\d{2})/(\d{4})", dmy or '')
                return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None

            if comp_vinc:
                # Saldo base: usar "Valor Original do Crédito Inicial" quando disponível;
                # fallback para valor do pedido e, por fim, soma dos débitos
                from decimal import Decimal
                from django.db import transaction
                soma_debitos = Decimal('0')
                for d in (parsed.debitos or []):
                    v = d.get('valor')
                    if v is not None:
                        try:
                            soma_debitos += Decimal(str(v))
                        except Exception:
                            pass
                saldo_base = getattr(parsed, 'valor_original_credito_inicial', None)
                if saldo_base is None:
                    saldo_base = parsed.valor_pedido if parsed.valor_pedido is not None else soma_debitos
                try:
                    with transaction.atomic():
                        ad = Adesao.objects.create(
                            cliente=cliente,
                            perdcomp=parsed.perdcomp or '',
                            metodo_credito=parsed.metodo_credito,
                            data_inicio=_conv_date(parsed.data_criacao) or timezone.now().date(),
                            saldo=float(saldo_base or 0),
                            ano=parsed.ano or None,
                            trimestre=parsed.trimestre or None,
                            tipo_credito=(parsed.tipo_credito or '')[:200] or None,
                            periodo_apuracao_credito=parsed.periodo_apuracao_credito or None,
                            codigo_receita=(parsed.codigo_receita or '')[:100] or None,
                        )
                        from django.utils import timezone as dj_tz
                        for d in (parsed.debitos or []):
                            val = d.get('valor')
                            if val is None:
                                continue
                            Lancamentos.objects.create(
                                id_adesao=ad,
                                data_lancamento=dj_tz.now(),
                                valor=float(val),
                                sinal='-',
                                tipo='Gerado',
                                descricao='Débito vinculado (importado do PDF) - Declaração de Compensação',
                                metodo=parsed.metodo_credito,
                                codigo_receita_denominacao=(d.get('codigo_receita_denominacao') or None),
                                periodo_apuracao_debito=(d.get('periodo_apuracao_debito') or None),
                                aprovado=True,
                            )
                    detail_url = reverse('adesao:detail', kwargs={'pk': ad.pk})
                    res = {'file': f.name, 'ok': True, 'created': True, 'id': ad.pk, 'detail_url': detail_url}
                except Exception as e:
                    res = {'file': f.name, 'ok': False, 'error': f'Falha ao criar adesão e débitos: {e}'}
                results.append(res)
                context_log['result'] = res
                write_log(f.name, context_log)
                continue
            else:
                # Fluxo padrão (Pedido de ressarcimento/restituição): usa o Form para validações
                form_data = {
                    'cliente': str(cliente.id),
                    'perdcomp': parsed.perdcomp or '',
                    'metodo_credito': parsed.metodo_credito or '',
                    'data_inicio': _conv_date(parsed.data_criacao) or '',
                    'saldo': str(parsed.valor_pedido) if parsed.valor_pedido is not None else '',
                    'ano': parsed.ano or '',
                    'trimestre': parsed.trimestre or '',
                    'tipo_credito': (parsed.tipo_credito or '')[:200],
                    'data_arrecadacao': _conv_date(parsed.data_arrecadacao) or '',
                    'periodo_apuracao_credito': parsed.periodo_apuracao_credito or '',
                    'codigo_receita': (parsed.codigo_receita or '')[:100],
                }
                form = AdesaoForm(data=form_data)
                if not form.is_valid():
                    errs = {k: [str(e) for e in v] for k, v in form.errors.items()}
                    res = {'file': f.name, 'ok': False, 'error': 'Falha na validação.', 'errors': errs}
                    results.append(res)
                    context_log['result'] = res
                    write_log(f.name, context_log)
                    continue
                obj = form.save()
                detail_url = reverse('adesao:detail', kwargs={'pk': obj.pk})
                res = {'file': f.name, 'ok': True, 'created': True, 'id': obj.pk, 'detail_url': detail_url}
                results.append(res)
                context_log['result'] = res
                write_log(f.name, context_log)
        except Exception as e:
            res = {'file': f.name, 'ok': False, 'error': f'Erro inesperado: {e}'}
            results.append(res)
            context_log['result'] = res
            write_log(f.name, context_log)
        finally:
            try:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

    return JsonResponse({'ok': True, 'results': results})


# Páginas
@login_required
@ensure_csrf_cookie
def importar_lote_page(request):
    # Permissão: staff/superuser ou permissão de adicionar adesão
    if not (request.user.is_superuser or request.user.is_staff or request.user.has_perm('adesao.add_adesao')):
        messages.error(request, 'Você não tem permissão para importar adesões em lote.')
        return redirect('adesao:list')
    return render(request, 'adesao/adesao_import_lote.html', {})


@login_required
def importacao_logs_page(request):
    # Permissão similar
    if not (request.user.is_superuser or request.user.is_staff or request.user.has_perm('adesao.view_adesao')):
        messages.error(request, 'Você não tem permissão para visualizar os logs de importação.')
        return redirect('adesao:list')
    import os, json, datetime
    from django.conf import settings
    logs_dir = os.path.join(getattr(settings, 'MEDIA_ROOT', ''), 'import_logs')
    entries = []
    try:
        if os.path.isdir(logs_dir):
            for fname in os.listdir(logs_dir):
                if not fname.endswith('.json'):
                    continue
                fpath = os.path.join(logs_dir, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fpath))
                    # Flatten a few useful fields
                    result = data.get('result') or {}
                    entries.append({
                        'filename': data.get('filename') or fname,
                        'user': data.get('user'),
                        'when': mtime,
                        'parsed': data.get('parsed', {}),
                        'ok': result.get('ok'),
                        'error': result.get('error'),
                        'detail_url': result.get('detail_url'),
                        'created': result.get('created'),
                        'raw_name': fname,
                    })
                except Exception:
                    continue
        # Sort desc by when
        entries.sort(key=lambda e: e['when'], reverse=True)
    except Exception:
        messages.error(request, 'Falha ao ler logs de importação.')
    return render(request, 'adesao/adesao_import_logs.html', {'entries': entries})

