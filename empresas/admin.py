from django.contrib import admin
from empresas.models import Empresa
from contatos.models import Contatos
from django.utils.safestring import mark_safe

class ContatosInline(admin.TabularInline):
    model = Contatos
    fk_name = 'empresa_base'  # Especifica qual campo ForeignKey usar
    extra = 1  # Número de formulários vazios a serem exibidos
    verbose_name = "Contato"
    verbose_name_plural = "Contatos"
    fields = ('tipo_contato', 'empresa_vinculada', 'telefone', 'email', 'site')

class ContatosVinculadosInline(admin.TabularInline):
    model = Contatos
    fk_name = 'empresa_vinculada'  # Especifica o outro campo ForeignKey
    extra = 0  # Apenas mostrar contatos existentes
    verbose_name = "Contato de Empresa Vinculada"
    verbose_name_plural = "Contatos de Empresas Vinculadas"
    fields = ('tipo_contato', 'empresa_base', 'telefone', 'email', 'site')
    readonly_fields = ('tipo_contato', 'empresa_base', 'telefone', 'email', 'site')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False  # Impedir adição através deste inline

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('cnpj', 'razao_social', 'nome_fantasia', 'codigo_origem', 'has_logo', 'contatos_count')
    list_filter = ('codigo_origem',)
    search_fields = ('cnpj', 'razao_social', 'nome_fantasia')
    readonly_fields = ('display_logomarca',)
    inlines = [ContatosInline, ContatosVinculadosInline]
    fieldsets = (
        ('Informações Principais', {
            'fields': ('cnpj', 'razao_social', 'nome_fantasia')
        }),
        ('Informações Adicionais', {
            'fields': ('codigo_origem', 'logomarca', 'display_logomarca'),
            'classes': ('collapse',)
        }),
    )
    
    def has_logo(self, obj):
        return bool(obj.logomarca)
    has_logo.boolean = True
    has_logo.short_description = 'Logo'
    
    def display_logomarca(self, obj):
        if obj.logomarca:
            return mark_safe(f'<img src="{obj.logomarca.url}" width="150" />')
        return "Sem logomarca"
    display_logomarca.short_description = 'Visualização da Logomarca'
    
    def contatos_count(self, obj):
        return obj.empresa_base_contato.count()
    contatos_count.short_description = 'Contatos'

# Registrando o modelo Contatos no admin também
@admin.register(Contatos)
class ContatosAdmin(admin.ModelAdmin):
    list_display = ('tipo_contato', 'empresa_base', 'empresa_vinculada', 'telefone', 'email')
    list_filter = ('tipo_contato',)
    search_fields = ('telefone', 'email', 'empresa_base__razao_social', 'empresa_vinculada__razao_social')