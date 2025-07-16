from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import UserProfile
from clientes_parceiros.models import ClientesParceiros

class UserProfileInline(admin.StackedInline):
    """Inline para exibir/editar perfil do usuário junto com o usuário"""
    model = UserProfile
    can_delete = False
    verbose_name = 'Perfil de Acesso'
    verbose_name_plural = 'Perfil de Acesso'
    
    fieldsets = (
        ('Vinculação Empresarial', {
            'fields': ('relacionamento', 'telefone', 'ativo'),
            'description': 'Configure o relacionamento empresarial do usuário'
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'relacionamento',
            'relacionamento__id_company_base',
            'relacionamento__id_company_vinculada',
            'relacionamento__id_tipo_relacionamento'
        )

class UserAdmin(BaseUserAdmin):
    """Admin customizado para User com perfil integrado"""
    inlines = (UserProfileInline,)
    
    list_display = ('username', 'get_full_name', 'email', 'get_empresa_base', 
                    'get_tipo_acesso', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'date_joined', 'profile__ativo')
    search_fields = ('username', 'first_name', 'last_name', 'email',
                    'profile__relacionamento__id_company_base__razao_social',
                    'profile__relacionamento__id_company_vinculada__razao_social')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'profile',
            'profile__relacionamento',
            'profile__relacionamento__id_company_base',
            'profile__relacionamento__id_company_vinculada',
            'profile__relacionamento__id_tipo_relacionamento'
        )
    
    def get_empresa_base(self, obj):
        """Exibe a empresa base do usuário"""
        try:
            if hasattr(obj, 'profile') and obj.profile.relacionamento:
                empresa = obj.profile.relacionamento.id_company_base
                return format_html(
                    '<span title="{}">{}</span>',
                    empresa.razao_social,
                    empresa.nome_fantasia or empresa.razao_social[:30]
                )
        except (AttributeError, UserProfile.DoesNotExist):
            pass
        return format_html('<span class="text-muted">Não vinculado</span>')
    get_empresa_base.short_description = 'Empresa Base'
    get_empresa_base.admin_order_field = 'profile__relacionamento__id_company_base__nome_fantasia'
    
    def get_tipo_acesso(self, obj):
        """Exibe o tipo de acesso do usuário"""
        try:
            if hasattr(obj, 'profile') and obj.profile.relacionamento:
                tipo = obj.profile.relacionamento.id_tipo_relacionamento.tipo_relacionamento
                if 'cliente' in tipo.lower():
                    return format_html('<span class="badge badge-primary">👤 Cliente</span>')
                elif 'parceiro' in tipo.lower():
                    return format_html('<span class="badge badge-success">🤝 Parceiro</span>')
                return format_html('<span class="badge badge-secondary">{}</span>', tipo)
        except (AttributeError, UserProfile.DoesNotExist):
            pass
        return format_html('<span class="text-muted">Sem acesso</span>')
    get_tipo_acesso.short_description = 'Tipo de Acesso'
    get_tipo_acesso.admin_order_field = 'profile__relacionamento__id_tipo_relacionamento__tipo_relacionamento'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin para gerenciar perfis de usuário diretamente"""
    list_display = ('get_usuario', 'get_empresa_base', 'get_empresa_vinculada', 
                    'get_tipo_relacionamento', 'telefone', 'ativo', 'data_criacao')
    list_filter = ('ativo', 'data_criacao', 
                   'relacionamento__id_tipo_relacionamento__tipo_relacionamento')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 
                    'user__email', 'telefone',
                    'relacionamento__id_company_base__razao_social',
                    'relacionamento__id_company_vinculada__razao_social')
    raw_id_fields = ('user', 'relacionamento')
    readonly_fields = ('data_criacao',)
    
    fieldsets = (
        ('Usuário', {
            'fields': ('user',)
        }),
        ('Vinculação Empresarial', {
            'fields': ('relacionamento',),
            'description': 'Selecione o relacionamento que define as empresas e tipo de acesso'
        }),
        ('Informações Adicionais', {
            'fields': ('telefone', 'ativo', 'data_criacao'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user',
            'relacionamento',
            'relacionamento__id_company_base',
            'relacionamento__id_company_vinculada',
            'relacionamento__id_tipo_relacionamento'
        )
    
    def get_usuario(self, obj):
        """Exibe informações do usuário"""
        user = obj.user
        nome = user.get_full_name() or user.username
        return format_html(
            '<strong>{}</strong><br><small class="text-muted">{}</small>',
            nome,
            user.email or user.username
        )
    get_usuario.short_description = 'Usuário'
    get_usuario.admin_order_field = 'user__username'
    
    def get_empresa_base(self, obj):
        """Exibe a empresa base"""
        if obj.relacionamento and obj.relacionamento.id_company_base:
            empresa = obj.relacionamento.id_company_base
            return format_html(
                '<span title="{}">{}</span>',
                empresa.razao_social,
                empresa.nome_fantasia or empresa.razao_social[:30]
            )
        return '-'
    get_empresa_base.short_description = 'Empresa Base'
    get_empresa_base.admin_order_field = 'relacionamento__id_company_base__nome_fantasia'
    
    def get_empresa_vinculada(self, obj):
        """Exibe a empresa vinculada"""
        if obj.relacionamento and obj.relacionamento.id_company_vinculada:
            empresa = obj.relacionamento.id_company_vinculada
            return format_html(
                '<span title="{}">{}</span>',
                empresa.razao_social,
                empresa.nome_fantasia or empresa.razao_social[:30]
            )
        return '-'
    get_empresa_vinculada.short_description = 'Empresa Vinculada'
    get_empresa_vinculada.admin_order_field = 'relacionamento__id_company_vinculada__nome_fantasia'
    
    def get_tipo_relacionamento(self, obj):
        """Exibe o tipo de relacionamento"""
        if obj.relacionamento and obj.relacionamento.id_tipo_relacionamento:
            tipo = obj.relacionamento.id_tipo_relacionamento.tipo_relacionamento
            if 'cliente' in tipo.lower():
                return format_html('<span style="color: #007bff;">👤 {}</span>', tipo)
            elif 'parceiro' in tipo.lower():
                return format_html('<span style="color: #28a745;">🤝 {}</span>', tipo)
            return tipo
        return '-'
    get_tipo_relacionamento.short_description = 'Tipo de Relacionamento'
    get_tipo_relacionamento.admin_order_field = 'relacionamento__id_tipo_relacionamento__tipo_relacionamento'

# Desregistrar o User admin padrão e registrar o customizado
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
