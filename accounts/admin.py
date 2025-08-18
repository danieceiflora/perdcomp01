from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django import forms
from .models import UserProfile
from clientes_parceiros.models import ClientesParceiros

# Formulário que adiciona campos do perfil diretamente
class CustomUserForm(forms.ModelForm):
    # Campos do perfil como parte do formulário do usuário
    relacionamento = forms.ModelChoiceField(
        queryset=ClientesParceiros.objects.all(),
        required=False,
        label='Relacionamento Empresarial'
    )
    telefone = forms.CharField(max_length=20, required=False, label='Telefone')
    perfil_ativo = forms.BooleanField(required=False, initial=True, label='Perfil Ativo')
    
    class Meta:
        model = User
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Preenche os campos do perfil se o usuário já existe
        if self.instance.pk:
            try:
                profile = UserProfile.objects.get(user=self.instance)
                self.fields['relacionamento'].initial = profile.relacionamento
                self.fields['telefone'].initial = profile.telefone
                self.fields['perfil_ativo'].initial = profile.ativo
            except UserProfile.DoesNotExist:
                pass
    
    def save(self, commit=True):
        user = super().save(commit)
        if commit:
            # Cria ou atualiza o perfil
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.relacionamento = self.cleaned_data.get('relacionamento')
            profile.telefone = self.cleaned_data.get('telefone', '')
            profile.ativo = self.cleaned_data.get('perfil_ativo', True)
            profile.save()
        return user
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'relacionamento',
            'relacionamento__id_company_base',
            'relacionamento__id_company_vinculada'
        )

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil do Usuário'
    fk_name = 'user'

class UserAdmin(BaseUserAdmin):
    """Admin customizado para User com perfil integrado"""
    form = CustomUserForm
    inlines = [UserProfileInline]
    
    # Sobrescreve get_form para garantir que os campos customizados sejam reconhecidos
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return form
    
    fieldsets = (
        (None, {
            'fields': (
                'username', 'password',
                'first_name', 'last_name', 'email',
                'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions',
                'last_login', 'date_joined'
            )
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'password1', 'password2',
                'first_name', 'last_name', 'email',
                'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions',
            ),
        }),
    )
    
    list_display = (
        'username', 'get_full_name', 'email', 'get_empresa_base', 
        'get_tipo_acesso', 'is_active', 'date_joined'
    )
    list_filter = ('is_active', 'is_staff', 'date_joined', 'profile__ativo')
    search_fields = (
        'username', 'first_name', 'last_name', 'email',
        'profile__relacionamento__id_company_base__razao_social',
        'profile__relacionamento__id_company_vinculada__razao_social'
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'profile',
            'profile__relacionamento',
            'profile__relacionamento__id_company_base',
            'profile__relacionamento__id_company_vinculada'
        )
    
    def get_empresa_base(self, obj):
        """Exibe a empresa base do usuário"""
        try:
            if hasattr(obj, 'profile') and obj.profile.relacionamento:
                empresa = obj.profile.relacionamento.id_company_base
                return format_html(
                    '<span title="{}">{}</span>',
                    empresa.razao_social,
                    empresa.nome_fantasia or empresa.razao_social[:30]
                )
        except (AttributeError, UserProfile.DoesNotExist):
            pass
        return format_html('<span class="text-muted">Não vinculado</span>')
    get_empresa_base.short_description = 'Empresa Base'
    get_empresa_base.admin_order_field = 'profile__relacionamento__id_company_base__razao_social'
    
    def get_tipo_acesso(self, obj):
        """Exibe o tipo de acesso do usuário"""
        try:
            if hasattr(obj, 'profile') and obj.profile.relacionamento:
                tipo = obj.profile.relacionamento.tipo_parceria
                if tipo == 'cliente':
                    return format_html('<span class="badge bg-primary">👤 Cliente</span>')
                elif tipo == 'parceiro':
                    return format_html('<span class="badge bg-success">🤝 Parceiro</span>')
                return format_html('<span class="badge bg-secondary">{}</span>', tipo)
        except (AttributeError, UserProfile.DoesNotExist):
            pass
        return format_html('<span class="text-muted">Sem acesso</span>')
    get_tipo_acesso.short_description = 'Tipo de Acesso'
    get_tipo_acesso.admin_order_field = 'profile__relacionamento__tipo_parceria'

# Desregistrar o User admin padrão e registrar o customizado
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# UserProfile será gerenciado apenas através do inline do User
# Removido o registro separado para evitar duplicação
