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
    
    # Impede a edição de qualquer lançamento no admin
    def has_change_permission(self, request, obj=None):
        # Retorna False para impedir qualquer edição
        # Poderia adicionar exceção para superusuários se necessário:
        # if request.user.is_superuser:
        #     return True
        return False
    
    # Impede a exclusão de qualquer lançamento no admin
    def has_delete_permission(self, request, obj=None):
        # Retorna False para impedir qualquer exclusão
        # Poderia adicionar exceção para superusuários se necessário:
        # if request.user.is_superuser:
        #     return True
        return False
    
    # Como não permitimos edição, todos os campos serão somente leitura
    # mas mantemos este método para mostrar os campos como era antes
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
    
    # Impede a edição de anexos no admin
    def has_change_permission(self, request, obj=None):
        return False
        
    # Impede a exclusão de anexos no admin
    def has_delete_permission(self, request, obj=None):
        return False
