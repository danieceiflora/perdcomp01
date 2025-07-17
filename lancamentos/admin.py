from django.contrib import admin
from django.contrib.admin.widgets import AdminDateWidget
from .models import Lancamentos, Anexos

from django import forms

# Inline para Anexos
class AnexosInline(admin.StackedInline):
    model = Anexos
    extra = 1
    fields = ('nome_anexo', 'descricao', 'arquivo')
    verbose_name = "Anexo"
    verbose_name_plural = "Anexos"

# Formulário personalizado para Lancamentos
class LancamentoAdminForm(forms.ModelForm):
    class Meta:
        model = Lancamentos
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        

# Versão simplificada do Admin para Lancamentos
@admin.register(Lancamentos)
class LancamentosAdmin(admin.ModelAdmin):
    form = LancamentoAdminForm
    list_display = ('id', 'id_adesao', 'data_lancamento', 'valor', 'sinal')
    list_filter = ('sinal',)
    search_fields = ('id_adesao__perdcomp',)
    readonly_fields = ('data_criacao', 'saldo_restante')
    inlines = [AnexosInline]
    
    # Método básico para controlar permissões
    def has_delete_permission(self, request, obj=None):
        return super().has_delete_permission(request, obj)
    
    # Método básico para campos somente leitura baseados no status
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        return readonly
            
    # Modificar o formulário em tempo real com JavaScript
    class Media:
        js = ('lancamentos/js/admin_lancamentos.js',)

# Versão simplificada do Admin para Anexos
@admin.register(Anexos)
class AnexosAdmin(admin.ModelAdmin):
    list_display = ('nome_anexo', 'id_lancamento', 'descricao', 'data_upload')
    list_filter = ('data_upload',)
    search_fields = ('nome_anexo', 'descricao')
    readonly_fields = ('data_upload',)
