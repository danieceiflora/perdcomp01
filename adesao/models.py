from django.db import models
from clientes_parceiros.models import ClientesParceiros
from correcao.models import TeseCredito

class Adesao(models.Model):
    cliente = models.ForeignKey(
        ClientesParceiros,
        on_delete=models.CASCADE,
        related_name='adesoes'
    )

    tese_credito_id = models.ForeignKey(
        TeseCredito,
        on_delete=models.CASCADE,
        related_name='adesoes',
        verbose_name='Tese de Crédito'
    )

    data_inicio = models.DateField(
        verbose_name='Data de Início',
        help_text='Data em que a adesão foi iniciada'
    )
    
    perdcomp = models.CharField(
        max_length=30,
        verbose_name='PERDCOMP'
    )

    saldo = models.FloatField(
        verbose_name='Saldo Inicial'
    )
    
    fee_rate = models.FloatField(
        verbose_name='Fee Rate'
    )

    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )
    saldo_atual = models.FloatField(
        verbose_name='Saldo Atual',
        help_text='Saldo atual da adesão, atualizado automaticamente pelos lançamentos',
        blank=True,
        null=True
    )
    
    def save(self, *args, **kwargs):
        """Sobrescreve o método save para garantir que o saldo_atual seja inicializado corretamente"""
        # Se é um novo objeto (não tem ID) e o saldo_atual não foi definido
        if not self.pk and not self.saldo_atual:
            self.saldo_atual = self.saldo
        super().save(*args, **kwargs)
    
    @property
    def empresa_cliente(self):
        """Acesso direto à empresa cliente vinculada"""
        return self.cliente.id_company_vinculada

    def __str__(self):
        if hasattr(self.cliente, 'id_company_vinculada'):
            empresa = self.empresa_cliente
            nome_empresa = empresa.nome_fantasia or empresa.razao_social
            return f"{self.perdcomp} - {nome_empresa}"
        return f"{self.perdcomp} - N/A"
    
    class Meta:
        verbose_name = 'Adesão'
        verbose_name_plural = 'Adesões'
    
