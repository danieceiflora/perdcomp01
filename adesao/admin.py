from django.contrib import admin
from django.utils.html import format_html
from .models import Adesao

@admin.register(Adesao)
class AdesaoAdmin(admin.ModelAdmin):
    list_display = ('perdcomp', 'cliente_info', 'tese_credito', 'data_inicio', 'saldo_inicial', 'saldo_atual_display', 'free_rate_display', 'ativo_display', 'lancamentos_count')
    list_filter = ('cliente__id_company_base', 'tese_credito_id__id_tipo_tese')
    search_fields = ('perdcomp', 'cliente__nome_referencia', 'cliente__empresa_vinculada__razao_social')
    
    
    fieldsets = (
        ('Identificação', {
            'fields': ('perdcomp', 'cliente', 'tese_credito_id')
        }),
        ('Valores', {
            'fields': ('saldo', 'saldo_atual', 'free_rate')
        }),
        ('Situação', {
            'fields': ('data_inicio', 'ativo')
        }),
    )
    
    def saldo_inicial(self, obj):
        if obj.saldo is None:
            return '-'
        try:
            valor_fmt = '{:.2f}'.format(float(obj.saldo))
            return format_html('R$ {}', valor_fmt)
        except (ValueError, TypeError):
            return format_html('R$ {}', str(obj.saldo))
    saldo_inicial.short_description = 'Saldo Inicial'
    
    def saldo_atual_display(self, obj):
        if obj.saldo_atual is None:
            return '-'
        try:
            saldo_float = float(obj.saldo_atual)
            color = 'green' if saldo_float > 0 else 'red' if saldo_float < 0 else 'gray'
            valor_fmt = '{:.2f}'.format(saldo_float)
            return format_html('<span style="color:{}; font-weight:bold">R$ {}</span>', 
                             color, valor_fmt)
        except (ValueError, TypeError):
            return format_html('<span>R$ {}</span>', str(obj.saldo_atual))
    saldo_atual_display.short_description = 'Saldo Atual'
    
    def free_rate_display(self, obj):
        if obj.free_rate is None:
            return '-'
        try:
            rate = float(obj.free_rate) / 100
            valor_fmt = '{:.2%}'.format(rate)
            return format_html('{}', valor_fmt)
        except (ValueError, TypeError):
            return format_html('{}%', str(obj.free_rate))
    free_rate_display.short_description = 'Free Rate'
    
    def cliente_info(self, obj):
        empresa = obj.cliente.id_company_vinculada.razao_social
        return f"{obj.cliente.nome_referencia} ({empresa})"
    cliente_info.short_description = 'Cliente'
    
    def tese_credito(self, obj):
        return obj.tese_credito_id.descricao
    tese_credito.short_description = 'Tese de Crédito'
    
    def ativo_display(self, obj):
        return format_html('<span style="color:{}; font-weight:bold">{}</span>', 
                         'green' if obj.ativo else 'red',
                         'Sim' if obj.ativo else 'Não')
    ativo_display.short_description = 'Ativo'
    
    def lancamentos_count(self, obj):
        return obj.lancamentos.count()
    lancamentos_count.short_description = 'Lançamentos'
