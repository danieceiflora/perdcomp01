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
    
    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'
