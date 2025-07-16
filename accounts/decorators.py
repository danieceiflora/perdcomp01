from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from functools import wraps
from django.contrib import messages
from accounts.permissions import eh_cliente_apenas_visualizacao
from lancamentos.models import Lancamentos
from adesao.models import Adesao

def cliente_can_view_lancamento(view_func):
    """
    Decorator para verificar se um cliente pode visualizar um lançamento específico.
    Só permite acesso se o cliente estiver associado à empresa vinculada ao lançamento.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden("Acesso negado. Você precisa estar logado.")
            
        # Se for superuser ou staff, permite acesso
        if request.user.is_superuser or request.user.is_staff:
            return view_func(request, *args, **kwargs)
            
        # Verifica se é um cliente com acesso apenas de visualização
        if eh_cliente_apenas_visualizacao(request.user):
            pk = kwargs.get('pk')
            if pk:
                lancamento = get_object_or_404(Lancamentos, pk=pk)
                empresa_lancamento = None
                
                if hasattr(lancamento, 'id_adesao') and lancamento.id_adesao:
                    if hasattr(lancamento.id_adesao, 'cliente') and lancamento.id_adesao.cliente:
                        if hasattr(lancamento.id_adesao.cliente, 'id_company_vinculada'):
                            empresa_lancamento = lancamento.id_adesao.cliente.id_company_vinculada
                
                # Se conseguimos identificar a empresa
                if empresa_lancamento:
                    # Verifica se o usuário pode acessar esta empresa
                    if request.user.profile.pode_acessar_empresa(empresa_lancamento.id):
                        return view_func(request, *args, **kwargs)
                        
        return HttpResponseForbidden("Acesso negado. Você não tem permissão para visualizar este lançamento.")
    
    return _wrapped_view

def cliente_can_view_adesao(view_func):
    """
    Decorator para verificar se um cliente pode visualizar uma adesão específica.
    Só permite acesso se o cliente estiver associado à empresa vinculada à adesão.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden("Acesso negado. Você precisa estar logado.")
            
        # Se for superuser ou staff, permite acesso
        if request.user.is_superuser or request.user.is_staff:
            return view_func(request, *args, **kwargs)
            
        # Verifica se é um cliente com acesso apenas de visualização
        if eh_cliente_apenas_visualizacao(request.user):
            pk = kwargs.get('pk')
            if pk:
                adesao = get_object_or_404(Adesao, pk=pk)
                empresa_adesao = None
                
                if hasattr(adesao, 'cliente') and adesao.cliente:
                    if hasattr(adesao.cliente, 'id_company_vinculada'):
                        empresa_adesao = adesao.cliente.id_company_vinculada
                
                # Se conseguimos identificar a empresa
                if empresa_adesao:
                    # Verifica se o usuário pode acessar esta empresa
                    if request.user.profile.pode_acessar_empresa(empresa_adesao.id):
                        return view_func(request, *args, **kwargs)
                        
        return HttpResponseForbidden("Acesso negado. Você não tem permissão para visualizar esta adesão.")
    
    return _wrapped_view

def admin_required(view_func):
    """
    Decorator para views baseadas em função que restringe o acesso a apenas administradores.
    Exibe uma página de acesso negado em vez de redirecionar.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            return view_func(request, *args, **kwargs)
            
        message = "Acesso negado. Somente administradores podem acessar esta página."
        messages.error(request, message)
        from django.shortcuts import render
        return render(
            request, 
            'forbidden.html', 
            {'message': message},
            status=403
        )
    return _wrapped_view
