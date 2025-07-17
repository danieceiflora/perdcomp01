from accounts.permissions import BasePermissionMixin, EmpresaAccessMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import Q

class LancamentoPermissionMixin(EmpresaAccessMixin):
    """
    Mixin específico para permissões de lançamentos para clientes e parceiros.
    """
    permission_denied_message = "Você só tem permissão para visualizar lançamentos permitidos para seu perfil."
    
    def get_empresas_por_adesao(self):
        
        """
        Método auxiliar que retorna IDs de empresas baseadas nas adesões
        que o usuário atual tem acesso.
        """
        user = self.request.user
        
        # Se é superuser ou staff, retorna None (acesso a tudo)
        if user.is_superuser or user.is_staff:
            return None
        
        # Se não tem perfil, nega acesso
        if not hasattr(user, 'profile'):
            return []
            
        profile = user.profile
        
        # Para clientes, retorna apenas sua própria empresa
        if profile.eh_cliente and profile.empresa_vinculada:
            print(f"Cliente acessando empresa: {profile.empresa_vinculada.id}")  # Debugging
            return [profile.empresa_vinculada.id]
        
        
        # Para parceiros, retorna empresas acessíveis
        empresas_acessiveis = profile.get_empresas_acessiveis()
        return [empresa.id for empresa in empresas_acessiveis]
    
    def get_queryset(self):
        """Filtra o queryset baseado no tipo de usuário"""
        queryset = super().get_queryset()
        
        # Obtém as empresas que o usuário tem acesso
        empresa_ids = self.get_empresas_por_adesao()
        print(f"Empresas acessíveis: {empresa_ids}")  # Debugging
        
        # Se é None, significa que é admin e tem acesso a tudo
        if empresa_ids is None:
            return queryset
            
        # Se é lista vazia, nega acesso a tudo
        if not empresa_ids:
            return queryset.none()
        
        # Acesso direto à tabela Adesao para consultar os IDs das adesões permitidas
        from adesao.models import Adesao
        
        # Obtém IDs de todas as adesões vinculadas às empresas permitidas
        adesao_ids = list(Adesao.objects.filter(
            cliente__id_company_vinculada__id__in=empresa_ids
        ).values_list('id', flat=True))

        print(f"IDs de adesões acessíveis: {adesao_ids}")  # Debugging

        
        
        # Se não encontrou adesões, nega acesso
        if not adesao_ids:
            return queryset.none()
            
        # Filtra o queryset usando os IDs de adesão
        debug = queryset.filter(id_adesao__id__in=adesao_ids)
        ##return queryset.filter(id_adesao__id__in=adesao_ids)
        print(debug)
        return debug
        
    def handle_no_permission(self):
        """Sobrescrito para mostrar página de erro em vez de redirecionar"""
        from django.shortcuts import render
        messages.error(self.request, self.permission_denied_message)
        return render(
            self.request, 
            'forbidden.html', 
            {'message': self.permission_denied_message},
            status=403
        )

# Mantém o nome antigo por compatibilidade
LancamentoClientePermissionMixin = LancamentoPermissionMixin

class LancamentoClienteViewOnlyMixin(LoginRequiredMixin):
    """
    Mixin específico para clientes que só podem visualizar lançamentos.
    Apenas restringe os métodos HTTP permitidos para clientes.
    """
    permission_denied_message = "Você só tem permissão para visualizar lançamentos permitidos para seu perfil."
    
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
