from django import forms
from clientes_parceiros.models import ClientesParceiros
from django.contrib import admin
from django.utils.html import format_html
from .models import ClientesParceiros
from django.core.exceptions import ValidationError

class ClientesParceirosAdminForm(forms.ModelForm):
    class Meta:
        model = ClientesParceiros
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tipo_id = None
        # Tenta obter o tipo de relacionamento do POST ou do objeto
        if self.data.get('id_tipo_parceria'):
            tipo_id = self.data.get('id_tipo_parceria')
        elif self.instance and self.instance.pk:
            tipo_id = getattr(self.instance, 'tipo_parceria_id', None)
        if tipo_id:
            empresas_vinculadas = ClientesParceiros.objects.filter(tipo_parceria=tipo_id).values_list('id_company_vinculada', flat=True)
            self.fields['id_company_vinculada'].queryset = self.fields['id_company_vinculada'].queryset.exclude(pk__in=empresas_vinculadas)


class ClientesParceirosInline(admin.TabularInline):
    model = ClientesParceiros
    fk_name = 'tipo_parceria'
    extra = 0
    fields = ('id_company_base', 'id_company_vinculada', 'nome_referencia', 'data_inicio_parceria', 'ativo')
    readonly_fields = ('data_inicio_parceria',)
    show_change_link = True


@admin.register(ClientesParceiros)
class ClientesParceirosAdmin(admin.ModelAdmin):
    form = ClientesParceirosAdminForm
    class Media:
        js = ('filter_empresas.js',)
    list_display = ('nome_referencia', 'cargo_referencia', 'empresa_base', 'empresa_vinculada', 
                   'tipo_relacionamento', 'status_ativo')
    list_filter = ('ativo', 'tipo_parceria',)
    search_fields = ('nome_referencia', 'cargo_referencia', 
                    'id_company_base__razao_social', 'id_company_vinculada__razao_social')
    fieldsets = (
        ('Informações da Parceria', {
            'fields': ('tipo_parceria', 'nome_referencia', 'cargo_referencia')
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
        return obj.tipo_parceria.tipo_relacionamento
    tipo_relacionamento.short_description = 'Tipo'

    def status_ativo(self, obj):
        return format_html('<span style="color:{};font-weight:bold">{}</span>', 
                          'green' if obj.ativo else 'red',
                          'Ativo' if obj.ativo else 'Inativo')
    status_ativo.short_description = 'Status'

    def save_model(self, request, obj, form, change):
        # Trava para não permitir empresa vinculada duplicada para o mesmo tipo de relacionamento
        if ClientesParceiros.objects.filter(
            id_company_vinculada=obj.id_company_vinculada,
            tipo_parceria=obj.tipo_parceria
        ).exclude(pk=obj.pk).exists():
            raise ValidationError("Esta empresa já está vinculada como cliente ou parceiro para este tipo de relacionamento.")
        super().save_model(request, obj, form, change)

