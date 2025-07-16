from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied

def eh_cliente_apenas_visualizacao(user):
    """
    Verifica se o usuário é um cliente com permissões apenas de visualização.
    
    Args:
        user: O usuário a ser verificado
        
    Returns:
        bool: True se o usuário for um cliente, False caso contrário
    """
    if not user.is_authenticated:
        return False
        
    # Superadmins e staff têm acesso total
    if user.is_superuser or user.is_staff:
        return False
        
    # Verifica se o usuário é um cliente
    if hasattr(user, 'profile') and user.profile.eh_cliente:
        return True
        
    return False

class BasePermissionMixin(LoginRequiredMixin):
    """Mixin base para todas as permissões"""
    permission_denied_message = "Você não tem permissão para acessar esta página."
    
    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return redirect('accounts:login_selector')

class ClienteRequiredMixin(BasePermissionMixin, UserPassesTestMixin):
    """Requer que o usuário seja um cliente"""
    permission_denied_message = "Acesso negado. Esta área é exclusiva para clientes."
    
    def test_func(self):
        if not hasattr(self.request.user, 'profile'):
            return False
        return self.request.user.profile.eh_cliente

class ParceiroRequiredMixin(BasePermissionMixin, UserPassesTestMixin):
    """Requer que o usuário seja um parceiro"""
    permission_denied_message = "Acesso negado. Esta área é exclusiva para parceiros."
    
    def test_func(self):
        if not hasattr(self.request.user, 'profile'):
            return False
        return self.request.user.profile.eh_parceiro

class EmpresaAccessMixin(BasePermissionMixin, UserPassesTestMixin):
    """Verifica se o usuário pode acessar dados de uma empresa específica"""
    permission_denied_message = "Você não tem permissão para acessar dados desta empresa."
    
    def test_func(self):
        # Obtém o ID da empresa dos parâmetros da URL
        empresa_id = self.kwargs.get('empresa_id') or self.kwargs.get('pk')
        
        # Se não houver empresa_id na URL, será verificado no get_object()
        if not empresa_id:
            return True
            
        # Verifica se o usuário tem acesso a esta empresa
        return self.request.user.profile.pode_acessar_empresa(empresa_id)
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        
        # Tenta encontrar a empresa relacionada ao objeto
        empresa = None
        
        if hasattr(obj, 'empresa'):
            empresa = obj.empresa
        elif hasattr(obj, 'id_company_vinculada'):
            empresa = obj.id_company_vinculada
        elif hasattr(obj, 'empresa_vinculada'):
            empresa = obj.empresa_vinculada
            
        # Verifica permissão para acessar esta empresa
        if empresa and not self.request.user.profile.pode_acessar_empresa(empresa.id):
            raise PermissionDenied(self.permission_denied_message)
            
        return obj

class ClienteViewOnlyMixin(ClienteRequiredMixin):
    """
    Restringe clientes a apenas visualizar (sem editar, adicionar ou excluir)
    """
    permission_denied_message = "Clientes têm permissão apenas para visualização."
    
    def dispatch(self, request, *args, **kwargs):
        # Permite apenas métodos GET (visualização)
        if request.method != 'GET':
            messages.error(request, self.permission_denied_message)
            return redirect('accounts:cliente_dashboard')
        return super().dispatch(request, *args, **kwargs)
