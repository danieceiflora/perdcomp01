from accounts.permissions import BasePermissionMixin, EmpresaAccessMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist

class AdesaoPermissionMixin(EmpresaAccessMixin):
    """
    Mixin específico para permissões de adesão para clientes e parceiros.
    - Para clientes: Restringe a apenas visualizar suas próprias adesões
    - Para parceiros: Permite visualizar adesões de todos os seus clientes
    - Verifica se o usuário tem acesso à empresa associada à adesão
    """
    permission_denied_message = "Você só tem permissão para visualizar adesões permitidas para seu perfil."
    
    def get_queryset(self):
        """Filtra o queryset baseado no tipo de usuário (cliente ou parceiro)"""
        queryset = super().get_queryset()
        
        # Se é superuser ou staff, tem acesso a tudo
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset
            
        # Se não tem perfil, nega acesso
        try:
            profile = self.request.user.profile
        except (AttributeError, ObjectDoesNotExist):
            return queryset.none()
        empresas_acessiveis = profile.get_empresas_acessiveis()
        empresa_ids = [empresa.id for empresa in empresas_acessiveis]
        
        # Se não tem empresas acessíveis, nega acesso
        if not empresa_ids:
            return queryset.none()
            
        # Filtrar baseado no campo de empresa no modelo
        # Verifica diferentes possíveis campos de relacionamento com empresa
        if hasattr(queryset.model, 'cliente'):
            # Assumindo que adesão tem um campo 'cliente' que se relaciona com empresa
            # Filtra por empresa do cliente da adesão
            queryset = queryset.filter(cliente__id_company_vinculada__id__in=empresa_ids)
        elif hasattr(queryset.model, 'empresa_vinculada'):
            queryset = queryset.filter(empresa_vinculada__id__in=empresa_ids)
        elif hasattr(queryset.model, 'empresa'):
            queryset = queryset.filter(empresa__id__in=empresa_ids)
        elif hasattr(queryset.model, 'id_company_vinculada'):
            queryset = queryset.filter(id_company_vinculada__id__in=empresa_ids)
                
        return queryset

class AdesaoClienteViewOnlyMixin(AdesaoPermissionMixin):
    """
    Mixin específico para clientes que só podem visualizar adesões.
    Herda de AdesaoPermissionMixin mas adiciona restrição de apenas visualização.
    """
    
    def dispatch(self, request, *args, **kwargs):
        # Para clientes, permite apenas métodos GET (visualização)
        # Admins não passam pela restrição de método
        if request.user.is_superuser or request.user.is_staff:
            return super().dispatch(request, *args, **kwargs)

        is_cliente = False
        try:
            profile = request.user.profile
            is_cliente = getattr(profile, 'eh_cliente', False)
        except ObjectDoesNotExist:
            is_cliente = False

        if is_cliente:
            if request.method != 'GET':
                from django.contrib import messages
                from django.shortcuts import redirect
                messages.error(request, "Clientes têm permissão apenas para visualização.")
                return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)

# Mantém o nome antigo por compatibilidade
AdesaoClientePermissionMixin = AdesaoPermissionMixin

class AdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin que restringe o acesso a apenas administradores (staff ou superuser).
    Útil para views que só devem ser acessíveis por administradores, como a adição de adesões.
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
