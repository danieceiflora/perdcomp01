from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Lancamentos

class LancamentoInline(admin.TabularInline):
    model = Lancamentos
    fk_name = 'lancamento_original'
    verbose_name = "Estorno"
    verbose_name_plural = "Estornos"
    extra = 0
    fields = ('data_lancamento', 'valor', 'sinal', 'status', 'observacao')
    readonly_fields = ('data_lancamento', 'valor', 'sinal', 'status', 'observacao')
    can_delete = False
    show_change_link = True
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Lancamentos)
class LancamentosAdmin(admin.ModelAdmin):
    list_display = ('id', 'adesao_perdcomp', 'data_lancamento', 'valor_formatado', 'tipo_display', 
                  'status_display', 'saldo_restante_display', 'tem_anexos')
    list_filter = ('status', 'sinal', 'tipo')
    search_fields = ('id_adesao__perdcomp', 'observacao')
    date_hierarchy = 'data_lancamento'
    readonly_fields = ('data_criacao', 'data_confirmacao', 'lancamento_original_link', 'saldo_restante')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id_adesao', 'data_lancamento', 'valor', 'sinal', 'tipo')
        }),
        ('Situação', {
            'fields': ('status', 'observacao', 'saldo_restante')
        }),
        ('Histórico', {
            'fields': ('data_criacao', 'data_confirmacao', 'lancamento_original_link'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [LancamentoInline]
    
    def adesao_perdcomp(self, obj):
        return obj.id_adesao.perdcomp
    adesao_perdcomp.short_description = 'PERDCOMP'
    
    def valor_formatado(self, obj):
        if obj.valor is None:
            return '-'
        color = 'green' if obj.sinal == '+' else 'red'
        try:
            valor_fmt = '{:.2f}'.format(float(obj.valor))
            return format_html('<span style="color:{}; font-weight:bold">{} R$ {}</span>', 
                          color, obj.sinal, valor_fmt)
        except (ValueError, TypeError):
            return format_html('<span style="color:{}; font-weight:bold">{} R$ {}</span>', 
                          color, obj.sinal, str(obj.valor))
    valor_formatado.short_description = 'Valor'
    
    def tipo_display(self, obj):
        return obj.tipo or "-"
    tipo_display.short_description = 'Tipo'
    
    def status_display(self, obj):
        color_map = {
            'PENDENTE': 'orange',
            'CONFIRMADO': 'green',
            'ESTORNADO': 'red',
        }
        return format_html('<span style="color:{}; font-weight:bold">{}</span>', 
                          color_map.get(obj.status, 'gray'), obj.status)
    status_display.short_description = 'Status'
    
    def saldo_restante_display(self, obj):
        if obj.saldo_restante is None:
            return "-"
        try:
            saldo_float = float(obj.saldo_restante)
            color = 'green' if saldo_float > 0 else 'red' if saldo_float < 0 else 'gray'
            valor_fmt = '{:.2f}'.format(saldo_float)
            return format_html('<span style="color:{}; font-weight:bold">R$ {}</span>', 
                              color, valor_fmt)
        except (ValueError, TypeError):
            return format_html('<span>R$ {}</span>', str(obj.saldo_restante))
    saldo_restante_display.short_description = 'Saldo Restante'
    
    def tem_anexos(self, obj):
        # Assumindo que existe um relacionamento de anexos
        # Se não existir, você pode remover este método ou adaptar conforme necessário
        has_anexos = hasattr(obj, 'anexos') and obj.anexos.exists()
        return format_html('<span style="color:{}">{}</span>', 
                          'green' if has_anexos else 'gray',
                          'Sim' if has_anexos else '-')
    tem_anexos.short_description = 'Anexos'
    
    def lancamento_original_link(self, obj):
        if obj.lancamento_original:
            url = reverse('admin:lancamentos_lancamentos_change', args=[obj.lancamento_original.id])
            return format_html('<a href="{}">Lançamento #{}</a>', 
                              url, obj.lancamento_original.id)
        return "-"
    lancamento_original_link.short_description = 'Lançamento Original'
