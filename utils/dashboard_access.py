from typing import List, Dict, Any
from django.db.models import Sum
from empresas.models import Empresa
from clientes_parceiros.models import ClientesParceiros
from adesao.models import Adesao
from lancamentos.models import Lancamentos


def collect_empresas(profile) -> Dict[str, Any]:
    user = profile.user
    resultado = []
    parceiro_base = None
    seen = set()

    # Superuser vê todas
    if user.is_superuser:
        for e in Empresa.objects.all():
            if e.id not in seen:
                resultado.append({'empresa': e, 'origem': 'superuser', 'is_base': False})
                seen.add(e.id)
        return {'empresas': resultado, 'parceiro_base': None}

    # Parceiro: empresa_parceira + clientes
    if profile.empresa_parceira_id:
        base = profile.empresa_parceira
        parceiro_base = base
        clientes_qs = ClientesParceiros.objects.filter(
            id_company_base=base,
            tipo_parceria='cliente',
            ativo=True
        ).select_related('id_company_vinculada')
        for rel in clientes_qs:
            emp = rel.id_company_vinculada
            if emp.id not in seen:
                resultado.append({'empresa': emp, 'origem': 'parceiro-cliente', 'is_base': False})
                seen.add(emp.id)
        return {'empresas': resultado, 'parceiro_base': parceiro_base}

    # Cliente (manual)
    for e in profile.empresas.all():
        if e.id not in seen:
            resultado.append({'empresa': e, 'origem': 'manual', 'is_base': False})
            seen.add(e.id)

    # Sócio (participações)
    for e in profile.empresas_via_socio:
        if e.id not in seen:
            resultado.append({'empresa': e, 'origem': 'socio', 'is_base': False})
            seen.add(e.id)

    return {'empresas': resultado, 'parceiro_base': parceiro_base}


def aggregate_credito(empresas_info: List[Dict[str, Any]]):
    if not empresas_info:
        return {'credito_recuperado': 0.0, 'credito_utilizado': 0.0, 'saldo_credito': 0.0}

    # Identificar empresas que são clientes (as que aparecem como id_company_vinculada em vínculos cliente)
    empresa_ids = [item['empresa'].id for item in empresas_info]

    vinculos_clientes = ClientesParceiros.objects.filter(
        id_company_vinculada_id__in=empresa_ids,
        tipo_parceria='cliente',
        ativo=True
    )

    if not vinculos_clientes.exists():
        return {'credito_recuperado': 0.0, 'credito_utilizado': 0.0, 'saldo_credito': 0.0}

    adesoes = Adesao.objects.filter(cliente__in=vinculos_clientes)

    # Crédito Recuperado: soma do campo saldo original
    credito_recuperado = adesoes.aggregate(total=Sum('saldo'))['total'] or 0

    # Saldo de Crédito: soma saldo_atual
    saldo_credito = adesoes.aggregate(total=Sum('saldo_atual'))['total'] or 0

    # Crédito Utilizado: soma absoluta dos lançamentos com sinal '-'
    lanc_debitos = Lancamentos.objects.filter(id_adesao__in=adesoes, sinal='-').aggregate(total=Sum('valor'))['total'] or 0
    credito_utilizado = abs(lanc_debitos)

    return {
        'credito_recuperado': float(credito_recuperado or 0),
        'credito_utilizado': float(credito_utilizado or 0),
        'saldo_credito': float(saldo_credito or 0),
    }


def build_dashboard_context(profile):
    coleta = collect_empresas(profile)
    empresas_info = coleta['empresas']
    parceiro_base = coleta['parceiro_base']
    agregados = aggregate_credito(empresas_info)
    return {
        'tipo_usuario': profile.tipo_usuario,
        'empresas_total': len(empresas_info),
        'parceiro_base': parceiro_base,
        'empresas_info': empresas_info,
        **agregados,
    }


def metricas_por_empresa(empresa_id: int):
    """Calcula métricas (crédito recuperado, utilizado, saldo) apenas para uma empresa cliente específica.
    Retorna dicionário com valores float.
    """
    vinculos = ClientesParceiros.objects.filter(
        id_company_vinculada_id=empresa_id,
        tipo_parceria='cliente',
        ativo=True
    )
    if not vinculos.exists():
        return {'credito_recuperado': 0.0, 'credito_utilizado': 0.0, 'saldo_credito': 0.0}
    adesoes = Adesao.objects.filter(cliente__in=vinculos)
    from django.db.models import Sum
    credito_recuperado = adesoes.aggregate(total=Sum('saldo'))['total'] or 0
    saldo_credito = adesoes.aggregate(total=Sum('saldo_atual'))['total'] or 0
    lanc_debitos = Lancamentos.objects.filter(id_adesao__in=adesoes, sinal='-').aggregate(total=Sum('valor'))['total'] or 0
    credito_utilizado = abs(lanc_debitos or 0)
    return {
        'credito_recuperado': float(credito_recuperado or 0),
        'credito_utilizado': float(credito_utilizado or 0),
        'saldo_credito': float(saldo_credito or 0)
    }
