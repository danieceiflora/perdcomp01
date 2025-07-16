from accounts.permissions import ClienteViewOnlyMixin, EmpresaAccessMixin

class LancamentoClientePermissionMixin(ClienteViewOnlyMixin, EmpresaAccessMixin):
    """
    Mixin específico para permissões de lançamentos para clientes.
    - Requer que o usuário seja cliente (via ClienteViewOnlyMixin)
    - Restringe a apenas visualizar (sem editar, adicionar ou excluir)
    - Verifica se o cliente tem acesso à empresa associada ao lançamento
    """
    permission_denied_message = "Você só tem permissão para visualizar lançamentos da sua empresa."
    
    def get_queryset(self):
        """Filtra o queryset para mostrar apenas lançamentos da empresa do cliente"""
        queryset = super().get_queryset()
        
        # Se não é superuser ou staff, filtra pelo acesso da empresa
        if not (self.request.user.is_superuser or self.request.user.is_staff):
            empresas_acessiveis = self.request.user.profile.get_empresas_acessiveis()
            empresa_ids = [empresa.id for empresa in empresas_acessiveis]
            
            # Filtrar por empresa_vinculada se o modelo tiver este campo
            if hasattr(queryset.model, 'empresa_vinculada'):
                queryset = queryset.filter(empresa_vinculada__id__in=empresa_ids)
            elif hasattr(queryset.model, 'empresa'):
                queryset = queryset.filter(empresa__id__in=empresa_ids)
            elif hasattr(queryset.model, 'id_company_vinculada'):
                queryset = queryset.filter(id_company_vinculada__id__in=empresa_ids)
                
        return queryset
