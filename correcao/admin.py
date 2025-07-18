from django.contrib import admin
from .models import Correcao, tipoTese, TeseCredito

@admin.register(Correcao)
class CorrecaoAdmin(admin.ModelAdmin):
    list_display = ('descricao', '' 'fonte_correcao', 'teses_count')
    list_filter = ('cod_origem',)
    search_fields = ('descricao', 'fonte_correcao')
    ordering = ('descricao',)
    
    def teses_count(self, obj):
        return obj.tesecredito_set.count()
    teses_count.short_description = 'Teses'

@admin.register(tipoTese)
class TipoTeseAdmin(admin.ModelAdmin):
    list_display = ('id', 'descricao', 'teses_count')
    search_fields = ('descricao',)
    
    def teses_count(self, obj):
        return obj.tesecredito_set.count()
    teses_count.short_description = 'Teses'

class TeseInline(admin.TabularInline):
    model = TeseCredito
    extra = 0
    fields = ('cod_origem', 'descricao', 'corrige',)
    show_change_link = True

@admin.register(TeseCredito)
class TeseCreditoAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'tipo_tese', 'corrige_display', 'adesoes_count')
    list_filter = ('id_tipo_tese', 'corrige', 'id_correcao')
    search_fields = ('descricao', 'jurisprudencia')
    fieldsets = (
        ('Identificação', {
            'fields': ('descricao', 'id_tipo_tese','cod_origem')
        }),
        ('Correção', {
            'fields': ('id_correcao', 'corrige',)
        }),
        ('Detalhes', {
            'fields': ('jurisprudencia',)
        }),
    )
    
    def tipo_tese(self, obj):
        return obj.id_tipo_tese.descricao
    tipo_tese.short_description = 'Tipo de Tese'
    
    
    def corrige_display(self, obj):
        return 'Sim' if obj.corrige else 'Não'
    corrige_display.short_description = 'Aplica Correção'
    
    def adesoes_count(self, obj):
        return obj.adesoes.count()
    adesoes_count.short_description = 'Adesões'

# Atualizar as classes Admin para incluir inlines
CorrecaoAdmin.inlines = [TeseInline]
