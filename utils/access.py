from __future__ import annotations
from typing import Set

__all__ = [
    'get_empresas_ids_for_cliente',
    'get_clientes_ids_for_parceiro',
]

def get_empresas_ids_for_cliente(profile) -> Set[int]:
    """Retorna o conjunto de IDs de empresas que um cliente pode acessar.

    Inclui:
    - Empresas diretamente vinculadas ao perfil (profile.empresas)
    - Empresas acessíveis via sócio (profile.empresas_via_socio)
    """
    empresas_ids: Set[int] = set()
    try:
        empresas_ids.update(profile.empresas.values_list('id', flat=True))
    except Exception:
        pass
    try:
        empresas_ids.update(profile.empresas_via_socio.values_list('id', flat=True))
    except Exception:
        pass
    return empresas_ids


def get_clientes_ids_for_parceiro(profile) -> Set[int]:
    """Retorna o conjunto de IDs de empresas (clientes) vinculadas a um parceiro.

    Baseado em ClientesParceiros onde:
    - id_company_base == profile.empresa_parceira
    - tipo_parceria == 'cliente'
    """
    empresa_parceira_id = getattr(profile, 'empresa_parceira_id', None)
    if not empresa_parceira_id:
        return set()
    try:
        from clientes_parceiros.models import ClientesParceiros
    except Exception:
        return set()
    qs = ClientesParceiros.objects.filter(
        id_company_base_id=empresa_parceira_id,
        tipo_parceria='cliente'
    ).values_list('id_company_vinculada_id', flat=True)
    return set(qs)
