from django.contrib import admin
from django.utils.html import format_html
from .models import TipoRelacionamento, ClientesParceiros

@admin.register(TipoRelacionamento)
class TipoRelacionamentoAdmin(admin.ModelAdmin):
    list_display = ('tipo_relacionamento', 'count_parceiros')
    search_fields = ('tipo_relacionamento',)
    
    def count_parceiros(self, obj):
        count = obj.clientes_parceiros.count()
        return format_html('<span style="color:{}">{}</span>', 
                          'green' if count > 0 else 'gray', 
                          f"{count} parceria(s)")
    count_parceiros.short_description = 'Parcerias'

class ClientesParceirosInline(admin.TabularInline):
    model = ClientesParceiros
    fk_name = 'id_tipo_relacionamento'
    extra = 0
    fields = ('id_company_base', 'id_company_vinculada', 'nome_referencia', 'data_inicio_parceria', 'ativo')
    readonly_fields = ('data_inicio_parceria',)
    show_change_link = True

@admin.register(ClientesParceiros)
class ClientesParceirosAdmin(admin.ModelAdmin):
    list_display = ('nome_referencia', 'cargo_referencia', 'empresa_base', 'empresa_vinculada', 
                   'tipo_relacionamento', 'status_ativo')
    list_filter = ('ativo', 'id_tipo_relacionamento',)
    search_fields = ('nome_referencia', 'cargo_referencia', 
                    'id_company_base__razao_social', 'id_company_vinculada__razao_social')
    fieldsets = (
        ('Informações da Parceria', {
            'fields': ('id_tipo_relacionamento', 'nome_referencia', 'cargo_referencia')
        }),
        ('Empresas', {
            'fields': ('id_company_base', 'id_company_vinculada')
        }),
        ('Detalhes', {
            'fields': ('ativo',)
        }),
    )
    
    def empresa_base(self, obj):
        return obj.id_company_base.nome_fantasia or obj.id_company_base.razao_social
    empresa_base.short_description = 'Empresa Base'
    
    def empresa_vinculada(self, obj):
        return obj.id_company_vinculada.nome_fantasia or obj.id_company_vinculada.razao_social
    empresa_vinculada.short_description = 'Empresa Vinculada'
    
    def tipo_relacionamento(self, obj):
        return obj.id_tipo_relacionamento.tipo_relacionamento
    tipo_relacionamento.short_description = 'Tipo'
    
    
    def status_ativo(self, obj):
        return format_html('<span style="color:{};font-weight:bold">{}</span>', 
                          'green' if obj.ativo else 'red',
                          'Ativo' if obj.ativo else 'Inativo')
    status_ativo.short_description = 'Status'

# Atualizar o admin do TipoRelacionamento para incluir o inline
TipoRelacionamentoAdmin.inlines = [ClientesParceirosInline]
