from django.db import models
from django.contrib.auth.models import User
from django.db import models
from empresas.models import Empresa
from clientes_parceiros.models import ClientesParceiros

class UserProfile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='profile'
    )
    empresas = models.ManyToManyField(
        Empresa,
        verbose_name='Empresas Acessíveis',
        help_text='Empresas que o usuário pode visualizar e gerenciar.',
        blank=True
    )
    empresa_parceira = models.ForeignKey(
        Empresa,
        verbose_name='Empresa Parceira',
        help_text='Se definido, o usuário atua como parceiro e não pode ter empresas clientes.',
        blank=True,
        null=True,
        related_name='usuarios_parceiros',
        on_delete=models.SET_NULL
    )
    telefone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Telefone'
    )
    data_criacao = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.user.get_full_name() or self.user.username
            
    def get_empresas_acessiveis(self):
        """Retorna o queryset de empresas que o usuário pode acessar."""
        if self.user.is_superuser:
            return Empresa.objects.all()
        return self.empresas.all()
    
    def pode_acessar_empresa(self, empresa_id):
        """Verifica se pode acessar dados de uma empresa específica pelo ID."""
        if self.user.is_superuser:
            return True
            
        if isinstance(empresa_id, str) and empresa_id.isdigit():
            empresa_id = int(empresa_id)
            
        return self.empresas.filter(id=empresa_id).exists()

    @property
    def empresas_via_socio(self):
        if hasattr(self.user, 'socio') and self.user.socio:
            from empresas.models import Empresa  # import local para evitar ciclos na migração
            ids = self.user.socio.participacoes.filter(ativo=True).values_list('empresa_id', flat=True)
            return Empresa.objects.filter(id__in=ids)
        from empresas.models import Empresa
        return Empresa.objects.none()

    @property
    def empresas_todas(self):
        if self.user.is_superuser:
            from empresas.models import Empresa
            return Empresa.objects.all()
        # Se for parceiro (empresa_parceira definida) ignora lista de clientes
        if self.empresa_parceira_id:
            from empresas.models import Empresa
            return Empresa.objects.filter(id=self.empresa_parceira_id)
        # Union manual (clientes) + via sócio
        ids_manual = self.empresas.values_list('id', flat=True)
        ids_socio = self.empresas_via_socio.values_list('id', flat=True)
        from empresas.models import Empresa
        return Empresa.objects.filter(id__in=list(set(ids_manual) | set(ids_socio)))

    @property
    def is_parceiro(self):
        return bool(self.empresa_parceira_id)

    def clean(self):
        from django.core.exceptions import ValidationError
        # Regra: ou parceiro único OU múltiplos clientes (não ambos)
        if self.empresa_parceira_id and self.empresas.exists():
            raise ValidationError('Usuário parceiro não pode ter empresas clientes atribuídas.')
        # Se empresa_parceira definida, validar que ela é realmente um parceiro
        if self.empresa_parceira_id:
            if not ClientesParceiros.objects.filter(id_company_vinculada=self.empresa_parceira, tipo_parceria='parceiro').exists():
                raise ValidationError('A empresa selecionada não está classificada como parceiro.')

    @property
    def tipo_usuario(self):
        if self.is_parceiro:
            return 'Parceiro'
        # Considera qualquer empresa cliente manual ou via sócio como cliente
        if self.empresas.exists() or self.empresas_via_socio.exists():
            return 'Cliente'
        return 'Indefinido'

    # --- Propriedades de compatibilidade legada ---
    @property
    def eh_parceiro(self):
        """Compatibilidade com código legado que usava 'eh_parceiro'."""
        return self.is_parceiro

    @property
    def eh_cliente(self):
        """Compatibilidade com código legado que usava 'eh_cliente'.
        Define cliente como qualquer perfil que não seja parceiro e tenha empresas
        associadas (diretas ou via participação como sócio)."""
        return (not self.is_parceiro) and (self.empresas.exists() or self.empresas_via_socio.exists())

    @property
    def empresa_vinculada(self):
        """Compatibilidade: retorna uma única empresa 'principal' quando possível.
        - Se for parceiro: retorna empresa_parceira
        - Se tiver exatamente uma empresa cliente associada: retorna essa
        - Caso contrário: None (evita ambiguidade)"""
        if self.is_parceiro:
            return self.empresa_parceira
        if self.empresas.count() == 1:
            return self.empresas.first()
        return None

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Se virou parceiro, garante limpeza das empresas clientes (caso tenha sido setado via script, sem form)
        if self.empresa_parceira_id and self.empresas.exists():
            self.empresas.clear()
    
    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'
