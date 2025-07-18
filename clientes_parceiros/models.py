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
    data_inicio_parceria = models.DateField(auto_now_add=True, verbose_name="Data de Início da Parceria")
    ativo = models.BooleanField(default=True)

    class Meta:
        # Garante a unicidade da combinação entre empresa base, empresa vinculada e tipo de relacionamento
        unique_together = ['id_company_base', 'id_company_vinculada', 'id_tipo_relacionamento']
        # Opcional: mensagem de erro mais amigável para violação de unicidade
        verbose_name = 'Vínculo Empresarial'
        verbose_name_plural = 'Vínculos Empresariais'

    def save(self, *args, **kwargs):
        # Verifica se já existe um registro com a mesma combinação de empresa base, vinculada e tipo de vínculo
        vinculo_existe = ClientesParceiros.objects.filter(
            id_company_base=self.id_company_base,
            id_company_vinculada=self.id_company_vinculada,
            id_tipo_relacionamento=self.id_tipo_relacionamento
        ).exclude(pk=self.pk).exists()
        
        if vinculo_existe:
            from django.core.exceptions import ValidationError
            raise ValidationError(
                f"Já existe um vínculo do tipo '{self.id_tipo_relacionamento}' entre "
                f"'{self.id_company_base}' e '{self.id_company_vinculada}'."
            )
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id_company_vinculada.razao_social} - {self.id_tipo_relacionamento.tipo_relacionamento}"