from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django import forms
from .models import UserProfile
from empresas.models import Empresa
from clientes_parceiros.models import ClientesParceiros

class UserProfileInlineForm(forms.ModelForm):
    empresas = forms.ModelMultipleChoiceField(
        queryset=Empresa.objects.filter(clientes_parceiros_vinculada__tipo_parceria='cliente').distinct(),
        widget=admin.widgets.FilteredSelectMultiple('Empresas Clientes', is_stacked=False),
        required=False,
        label=''  # remove label ao lado do widget
    )

    class Meta:
        model = UserProfile
        fields = ('telefone', 'ativo', 'empresas')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Garante ausência de help-text redundante
        self.fields['empresas'].help_text = ''

    class Media:
        css = {
            'all': (
                # CSS inline para esconder qualquer label residual ou spacing
                'admin/custom_hide_empresas_label.css',
            )
        }

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    form = UserProfileInlineForm
    can_delete = False
    verbose_name_plural = 'Perfil e Empresas'
    fk_name = 'user'
    fieldsets = (
        (None, {
            'fields': (('telefone', 'ativo'),)
        }),
        (None, {  # sem título/legend para não gerar texto extra
            'fields': ('empresas',),
            'description': ''
        }),
    )

class UserAdmin(BaseUserAdmin):
    """Admin customizado para User com perfil integrado"""
    inlines = [UserProfileInline]
    
    list_display = (
        'username', 'get_full_name', 'email', 
        'display_empresas', 'is_active', 'date_joined'
    )
    list_filter = ('is_active', 'is_staff', 'date_joined', 'profile__ativo')
    search_fields = (
        'username', 'first_name', 'last_name', 'email',
        'profile__empresas__razao_social',
        'profile__empresas__nome_fantasia'
    )

    def display_empresas(self, obj):
        try:
            profile = obj.profile
            empresas = profile.empresas.all()
            if not empresas:
                return "Nenhuma empresa"
            
            if empresas.count() > 2:
                return f"{empresas.count()} empresas"

            return format_html("<br>".join([e.nome_fantasia or e.razao_social for e in empresas]))
        except UserProfile.DoesNotExist:
            return "Sem perfil"
    display_empresas.short_description = 'Empresas Acessíveis'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profile').prefetch_related('profile__empresas')

# Desregistra o UserAdmin padrão e registra o customizado
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'telefone', 'ativo', 'display_empresas')
    search_fields = ('user__username', 'user__first_name', 'user__email', 'empresas__razao_social')
    list_filter = ('ativo', 'empresas')
    filter_horizontal = ('empresas',)

    def display_empresas(self, obj):
        count = obj.empresas.count()
        if count == 0:
            return "Nenhuma"
        if count > 3:
            return f"{count} empresas"
        return ", ".join([e.nome_fantasia or e.razao_social for e in obj.empresas.all()])
    display_empresas.short_description = 'Empresas'
