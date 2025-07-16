from accounts.permissions import BasePermissionMixin, EmpresaAccessMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages

class LancamentoPermissionMixin(EmpresaAccessMixin):
    """
    Mixin específico para permissões de lançamentos para clientes e parceiros.
    - Para clientes: Restringe a apenas visualizar seus próprios lançamentos
    - Para parceiros: Permite visualizar lançamentos de todos os seus clientes
    - Verifica se o usuário tem acesso à empresa associada ao lançamento
    """
    permission_denied_message = "Você só tem permissão para visualizar lançamentos permitidos para seu perfil."
    
    def get_queryset(self):
        """Filtra o queryset baseado no tipo de usuário (cliente ou parceiro)"""
        queryset = super().get_queryset()
        
        # Se é superuser ou staff, tem acesso a tudo
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset
            
        # Se não tem perfil, nega acesso
        if not hasattr(self.request.user, 'profile'):
            return queryset.none()
            
        profile = self.request.user.profile
        empresas_acessiveis = profile.get_empresas_acessiveis()
        empresa_ids = [empresa.id for empresa in empresas_acessiveis]
        
        # Se não tem empresas acessíveis, nega acesso
        if not empresa_ids:
            return queryset.none()
            
        # Filtrar baseado no relacionamento com adesão e empresa
        # Lançamento -> Adesão -> Cliente -> Empresa
        if hasattr(queryset.model, 'id_adesao'):
            # Filtra lançamentos através da adesão -> cliente -> empresa
            queryset = queryset.filter(id_adesao__cliente__id_company_vinculada__id__in=empresa_ids)
        elif hasattr(queryset.model, 'adesao'):
            queryset = queryset.filter(adesao__cliente__id_company_vinculada__id__in=empresa_ids)
        elif hasattr(queryset.model, 'empresa_vinculada'):
            queryset = queryset.filter(empresa_vinculada__id__in=empresa_ids)
        elif hasattr(queryset.model, 'empresa'):
            queryset = queryset.filter(empresa__id__in=empresa_ids)
                
        return queryset

# Mantém o nome antigo por compatibilidade
LancamentoClientePermissionMixin = LancamentoPermissionMixin

class LancamentoClienteViewOnlyMixin(LancamentoPermissionMixin):
    """
    Mixin específico para clientes que só podem visualizar lançamentos.
    Herda de LancamentoPermissionMixin mas adiciona restrição de apenas visualização.
    """
    
    def dispatch(self, request, *args, **kwargs):
        # Para clientes, permite apenas métodos GET (visualização)
        if hasattr(request.user, 'profile') and request.user.profile.eh_cliente:
            if request.method != 'GET':
                from django.contrib import messages
                from django.shortcuts import redirect
                messages.error(request, "Clientes têm permissão apenas para visualização.")
                return redirect('accounts:cliente_dashboard')
        return super().dispatch(request, *args, **kwargs)

class AdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin que restringe o acesso a apenas administradores (staff ou superuser).
    Útil para views que só devem ser acessíveis por administradores, como a adição de lançamentos.
    Exibe uma mensagem de acesso negado em vez de redirecionar.
    """
    permission_denied_message = "Acesso negado. Somente administradores podem acessar esta página."
    
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser)
    
    def handle_no_permission(self):
        from django.shortcuts import render
        messages.error(self.request, self.permission_denied_message)
        return render(
            self.request, 
            'forbidden.html', 
            {'message': self.permission_denied_message},
            status=403
        )
