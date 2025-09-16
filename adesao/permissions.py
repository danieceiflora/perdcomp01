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
        """Filtra queryset conforme papel do usuário.
        - Admin/staff: tudo
        - Cliente: empresas diretas + via sócio
        - Parceiro: clientes vinculados à empresa_parceira (ClientesParceiros com tipo_parceria='cliente')
        """
        base = super().get_queryset()
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return base
        try:
            profile = user.profile
        except (AttributeError, ObjectDoesNotExist):
            return base.none()
        # Cliente
        if profile.eh_cliente:
            empresas_ids = set(profile.empresas.values_list('id', flat=True)) | set(profile.empresas_via_socio.values_list('id', flat=True))
            if not empresas_ids:
                return base.none()
            if hasattr(base.model, 'cliente'):
                return base.filter(cliente__id_company_vinculada_id__in=empresas_ids)
            return base.none()
        # Parceiro
        if profile.eh_parceiro and profile.empresa_parceira_id:
            from clientes_parceiros.models import ClientesParceiros
            clientes_ids = ClientesParceiros.objects.filter(
                id_company_base_id=profile.empresa_parceira_id,
                tipo_parceria='cliente'
            ).values_list('id_company_vinculada_id', flat=True)
            if not clientes_ids:
                return base.none()
            return base.filter(cliente__id_company_vinculada_id__in=clientes_ids)
        return base.none()

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
