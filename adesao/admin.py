from django.contrib import admin
from django.utils.html import format_html
from django import forms
from .models import Adesao
from clientes_parceiros.models import ClientesParceiros

class AdesaoAdminForm(forms.ModelForm):
    class Meta:
        model = Adesao
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Verifica se o campo 'cliente' existe no formulário
        # (pode não existir quando estamos apenas visualizando um objeto)
        if 'cliente' in self.fields:
            # Filtra apenas clientes (tipo_relacionamento=1) e ativos
            try:
                self.fields['cliente'].queryset = ClientesParceiros.objects.filter(
                    id_tipo_relacionamento__id=1,  # Apenas clientes
                    ativo=True
                ).select_related('id_company_vinculada')
            except Exception as e:
                print(f"Erro ao filtrar clientes no admin: {e}")
                self.fields['cliente'].queryset = ClientesParceiros.objects.none()

@admin.register(Adesao)
class AdesaoAdmin(admin.ModelAdmin):

    form = AdesaoAdminForm  # Usa o formulário personalizado
    list_display = ('perdcomp', 'cliente_info', 'tese_credito', 'data_inicio', 'saldo_inicial', 'saldo_atual_display', 'fee_rate_display', 'ativo_display', 'lancamentos_count')
    list_filter = ('cliente__id_company_base', 'tese_credito_id__id_tipo_tese')
    search_fields = ('perdcomp', 'cliente__nome_referencia', 'cliente__empresa_vinculada__razao_social')
    
    fields = ('perdcomp', 'cliente', 'tese_credito_id', 'saldo', 'saldo_atual', 'fee_rate', 'data_inicio', 'ativo')
    
    # Controla a permissão para edição
    def has_change_permission(self, request, obj=None):
        # Permitimos acesso à página de visualização/edição
        # (vamos tornar os campos somente leitura em vez de bloquear totalmente)
        return True
    
    # Impede a exclusão de adesões
    def has_delete_permission(self, request, obj=None):
        # Não permite exclusão de nenhuma adesão
        return False
        
    # Todos os campos serão somente leitura ao visualizar uma adesão existente
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Se estiver visualizando um objeto existente
            # Torna todos os campos somente leitura, incluindo 'cliente' e outros
            return list(self.fields)
        # Se for criação, nenhum campo é somente leitura, exceto os configurados anteriormente
        return []
        
    # Método para impedir a alteração de qualquer campo, mesmo permitindo visualização
    def save_model(self, request, obj, form, change):
        # Se estiver alterando um objeto existente (não criando um novo)
        if change:
            # Não fazemos nada, efetivamente impedindo qualquer alteração
            return
        # Caso contrário, permite a criação normalmente
        super().save_model(request, obj, form, change)
    
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
    
    def fee_rate_display(self, obj):
        if obj.fee_rate is None:
            return '-'
        try:
            rate = float(obj.fee_rate) / 100
            valor_fmt = '{:.2%}'.format(rate)
            return format_html('{}', valor_fmt)
        except (ValueError, TypeError):
            return format_html('{}%', str(obj.fee_rate))
    fee_rate_display.short_description = 'Fee Rate'
    
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
