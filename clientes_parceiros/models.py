from django.db import models
from empresas.models import Empresa
from simple_history.models import HistoricalRecords

class ClientesParceiros(models.Model):

    tipo_parceira_options = [
        ('cliente', 'Cliente'),
        ('parceiro', 'Parceiro'),
    ]

    tipo_parceria = models.CharField(
        max_length=10,
        choices=tipo_parceira_options,
        default='cliente',
        verbose_name="Tipo de Parceria"
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
    # Histórico (auditoria)
    historico = HistoricalRecords()

    class Meta:
        # Garante a unicidade da combinação entre empresa base, empresa vinculada e tipo de relacionamento
        unique_together = ['id_company_base', 'id_company_vinculada', 'tipo_parceria']
        # Opcional: mensagem de erro mais amigável para violação de unicidade
        verbose_name = 'Vínculo Empresarial'
        verbose_name_plural = 'Vínculos Empresariais'

    def save(self, *args, **kwargs):
        # Verifica se já existe um registro com a mesma combinação de empresa base, vinculada e tipo de vínculo
        vinculo_existe = ClientesParceiros.objects.filter(
            id_company_base=self.id_company_base,
            id_company_vinculada=self.id_company_vinculada,
            tipo_parceria=self.tipo_parceria
        ).exclude(pk=self.pk).exists()
        
        if vinculo_existe:
            from django.core.exceptions import ValidationError
            raise ValidationError(
                f"Já existe um vínculo do tipo '{self.tipo_parceria}' entre "
                f"'{self.id_company_base}' e '{self.id_company_vinculada}'."
            )
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id_company_vinculada.razao_social} - {self.tipo_parceria}"