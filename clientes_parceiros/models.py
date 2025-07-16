from django.db import models
from empresas.models import Empresa

class TipoRelacionamento(models.Model):
    tipo_relacionamento = models.CharField(max_length=50, unique=True, verbose_name="Vínculo")

    def __str__(self):
        return self.tipo_relacionamento
    
    class Meta:
        verbose_name = 'Vínculo'
        verbose_name_plural = 'Vínculos'

class ClientesParceiros(models.Model):
    id_tipo_relacionamento = models.ForeignKey(
        TipoRelacionamento, 
        on_delete=models.CASCADE, 
        related_name='clientes_parceiros',
        verbose_name="Vínculo"
    )
    id_company_base = models.ForeignKey(
        Empresa, 
        on_delete=models.CASCADE, 
        related_name='clientes_parceiros_base'
    )
    id_company_vinculada = models.ForeignKey(
        Empresa, 
        on_delete=models.CASCADE, 
        related_name='clientes_parceiros_vinculada'
    )
    nome_referencia = models.CharField(max_length=200)
    cargo_referencia = models.CharField(max_length=100, blank=True, null=True)
    # Alterando de DateTimeField para DateField
    data_inicio_parceria = models.DateField(blank=True, null=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.id_company_vinculada.razao_social} - {self.id_tipo_relacionamento.tipo_relacionamento}"