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

    metodo_credito_options = [
        ('Pedido de compensação', 'Pedido de compensação'),
        ('Pedido de restituição', 'Pedido de restituição'),
        ('Declaração de compensação', 'Declaração de compensação')
    ]

    metodo_credito = models.CharField(
        max_length=50,
        choices=metodo_credito_options,
        verbose_name='Método de Crédito',
        blank=True,
        null=True
    )

    data_inicio = models.DateField(
        verbose_name='Data de Início',
        help_text='Data em que a adesão foi iniciada'
    )
    
    perdcomp = models.CharField(
        max_length=30,
        verbose_name='PERDCOMP',
        blank=True,
        null=True,
    )

    saldo = models.FloatField(
        verbose_name='Valor do crédito',
    )
    
    ano_trimestre = models.CharField(
        max_length=7,
        verbose_name='Ano/Trimestre',
        blank=True,
        null=True,
    )

    periodo_apuracao = models.CharField(
        max_length=20,
        verbose_name='Período de Apuração',
        blank=True,
        null=True,
    )

    periodo_apuracao_um = models.CharField(
        max_length=20,
        verbose_name='Período de Apuração 1',
        blank=True,
        null=True,
    )

    codigo_receita = models.CharField(
        max_length=20,
        verbose_name='Código da Receita',
        blank=True,
        null=True,
    )

    codigo_receita_denominacao = models.CharField(
        max_length=20,
        verbose_name='Código Receita / Denominação',
        blank=True,
        null=True,
    )

    credito_original_utilizado = models.FloatField(
        verbose_name='Crédito Original Utilizado',
        blank=True,
        null=True,
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
    
