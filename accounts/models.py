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
    relacionamento = models.ForeignKey(
        ClientesParceiros,
        on_delete=models.CASCADE,
        verbose_name='Relacionamento Empresarial',
        help_text='Define o tipo de acesso e empresas vinculadas'
    )
    telefone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Telefone'
    )
    data_criacao = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.relacionamento}"
    
    @property
    def empresa_base(self):
        """Empresa onde o usuário trabalha"""
        return self.relacionamento.id_company_base
    
    @property  
    def empresa_vinculada(self):
        """Empresa que o usuário pode acessar"""
        return self.relacionamento.id_company_vinculada
    
    @property
    def tipo_relacionamento(self):
        """Tipo de relacionamento (cliente/parceiro)"""
        return self.relacionamento.id_tipo_relacionamento
    
    @property
    def eh_cliente(self):
        """Verifica se o usuário tem acesso como cliente"""
        return 'cliente' in self.tipo_relacionamento.tipo_relacionamento.lower()
    
    @property
    def eh_parceiro(self):
        """Verifica se o usuário tem acesso como parceiro"""
        return 'parceiro' in self.tipo_relacionamento.tipo_relacionamento.lower()
    
    def get_empresas_acessiveis(self):
        """Retorna empresas que o usuário pode acessar baseado no relacionamento"""
        if self.eh_parceiro:
            # Hierarquia: Empresa principal -> Parceiros -> Clientes
            # Parceiro vê todas as empresas clientes que sua empresa atende
            # Na tabela clientes_parceiros:
            # - id_company_base = empresa do parceiro (empresa_vinculada no perfil)
            # - id_company_vinculada = empresas clientes deste parceiro
            # - tipo_relacionamento contém "cliente"
            relacionamentos = ClientesParceiros.objects.filter(
                id_company_base=self.empresa_vinculada,  # Empresa do parceiro
                id_tipo_relacionamento__tipo_relacionamento__icontains='cliente',
                ativo=True
            )
            return [rel.id_company_vinculada for rel in relacionamentos]
        elif self.eh_cliente:
            # Cliente vê apenas dados da própria empresa
            return [self.empresa_vinculada]
        return []
    
    def pode_acessar_empresa(self, empresa):
        """Verifica se pode acessar dados de uma empresa específica"""
        return empresa in self.get_empresas_acessiveis()
    
    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'
