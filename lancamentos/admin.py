from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Lancamentos, Anexos

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

class AnexosInline(admin.TabularInline):
    model = Anexos
    extra = 1
    fields = ('nome_anexo', 'descricao', 'arquivo', 'data_upload')
    readonly_fields = ('data_upload',)
    verbose_name = "Anexo"
    verbose_name_plural = "Anexos"

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
    
    inlines = [AnexosInline, LancamentoInline]
    
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
        count = obj.anexos.count()
        if count > 0:
            return format_html('<span style="color:green; font-weight:bold">{} anexo(s)</span>', count)
        return format_html('<span style="color:gray">-</span>')
    tem_anexos.short_description = 'Anexos'
    
    def lancamento_original_link(self, obj):
        if obj.lancamento_original:
            url = reverse('admin:lancamentos_lancamentos_change', args=[obj.lancamento_original.id])
            return format_html('<a href="{}">Lançamento #{}</a>', 
                              url, obj.lancamento_original.id)
        return "-"
    lancamento_original_link.short_description = 'Lançamento Original'

@admin.register(Anexos)
class AnexosAdmin(admin.ModelAdmin):
    list_display = ('nome_anexo', 'lancamento_info', 'descricao', 'arquivo_link', 'data_upload')
    list_filter = ('data_upload', 'id_lancamento__status')
    search_fields = ('nome_anexo', 'descricao', 'id_lancamento__id_adesao__perdcomp')
    date_hierarchy = 'data_upload'
    readonly_fields = ('data_upload', 'arquivo_preview')
    
    fieldsets = (
        ('Informações do Anexo', {
            'fields': ('id_lancamento', 'nome_anexo', 'descricao')
        }),
        ('Arquivo', {
            'fields': ('arquivo', 'arquivo_preview', 'data_upload')
        }),
    )
    
    def lancamento_info(self, obj):
        return f"#{obj.id_lancamento.id} - {obj.id_lancamento.id_adesao.perdcomp}"
    lancamento_info.short_description = 'Lançamento'
    
    def arquivo_link(self, obj):
        if obj.arquivo:
            return format_html('<a href="{}" target="_blank">Baixar</a>', obj.arquivo.url)
        return '-'
    arquivo_link.short_description = 'Download'
    
    def arquivo_preview(self, obj):
        if obj.arquivo:
            file_name = obj.arquivo.name.split('/')[-1]
            return format_html(
                '<div style="border: 1px solid #ddd; padding: 10px; border-radius: 4px;">'
                '<strong>Arquivo:</strong> {}<br>'
                '<strong>Tamanho:</strong> {:.2f} KB<br>'
                '<a href="{}" target="_blank" style="color: #007cba;">Visualizar arquivo</a>'
                '</div>',
                file_name,
                obj.arquivo.size / 1024 if obj.arquivo.size else 0,
                obj.arquivo.url
            )
        return "Nenhum arquivo anexado"
    arquivo_preview.short_description = 'Visualização do Arquivo'
