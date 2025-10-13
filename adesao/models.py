from django.db import models
from clientes_parceiros.models import ClientesParceiros
from simple_history.models import HistoricalRecords

class Adesao(models.Model):
   
    cliente = models.ForeignKey(
        ClientesParceiros,
        on_delete=models.CASCADE,
        related_name='adesoes'
    )

    # Removido relacionamento com TeseCredito; usamos apenas texto em 'tipo_credito'

    metodo_credito_options = [
        ('Pedido de ressarcimento', 'Pedido de ressarcimento'),
        ('Pedido de restituição', 'Pedido de restituição'),
        ('Declaração de compensação pagamento indevido', 'Declaração de compensação pagamento indevido'),
        ('Escritural', 'Escritural'),
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
        verbose_name='PERDCOMP'
    )

    saldo = models.FloatField(
        verbose_name='Valor do crédito ',
    )

    # Armazena o primeiro dia do mês referente (entrada do usuário mm/aaaa)
    ano = models.CharField(
        verbose_name='Ano',
        max_length=4,
        blank=True,
        null=True,
    )

    trimestre_options = [
        ('1', '1º Trimestre'),
        ('2', '2º Trimestre'),
        ('3', '3º Trimestre'),
        ('4', '4º Trimestre'),
    ]

    trimestre = models.CharField(
        max_length=1,
        choices=trimestre_options,
        verbose_name='Trimestre',
        blank=True,
        null=True
    )

    periodo_apuracao_credito = models.CharField(
        max_length=20,
        verbose_name='Período de Apuração Crédito',
        blank=True,
        null=True,
    )

    periodo_apuracao_debito = models.CharField(
        max_length=20,
        verbose_name='Periodo apuração débito',
        blank=True,
        null=True,
    )

    tipo_credito = models.CharField(
        max_length=200,
        verbose_name='Tipo de Crédito',
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

    total = models.FloatField(
        verbose_name='Total',
        blank=True,
        null=True,
    )

    credito_original_utilizado = models.FloatField(
        verbose_name='Crédito Original Utilizado',
        blank=True,
        null=True,
    )

   

    valor_do_principal = models.FloatField(
        verbose_name='Valor do Principal',
        blank=True,
        null=True
    )


    saldo_atual = models.FloatField(
        verbose_name='Saldo Atual',
        help_text='Saldo atual da adesão, atualizado automaticamente pelos lançamentos',
        blank=True,
        null=True
    )

    # Campos específicos para Restituição (apenas informativos)
    selic_acumulada = models.FloatField(
        verbose_name='SELIC Acumulada (%)',
        help_text='Taxa SELIC acumulada para cálculo de correção - apenas informativo',
        blank=True,
        null=True
    )

    valor_correcao = models.FloatField(
        verbose_name='Valor da Correção',
        help_text='Valor da correção monetária aplicada - apenas informativo',
        blank=True,
        null=True
    )

    valor_total_corrigido = models.FloatField(
        verbose_name='Valor Total Corrigido',
        help_text='Valor principal + correção monetária - apenas informativo',
        blank=True,
        null=True
    )

    data_arrecadacao = models.DateField(
        verbose_name='Data de Arrecadação',
        help_text='Data em que ocorreu a arrecadação relacionada',
        blank=True,
        null=True
    )

    # Campos específicos para método Escriturial
    origem = models.CharField(
        max_length=255,
        verbose_name='Origem',
        help_text='Origem do crédito (escritural)',
        blank=True,
        null=True,
    )
    data_origem = models.DateField(
        verbose_name='Data de Origem',
        help_text='Data da origem do crédito (escritural)',
        blank=True,
        null=True,
    )

    # Audit trail
    historico = HistoricalRecords()
    
    def save(self, *args, **kwargs):
        """Sobrescreve o método save para garantir que o saldo_atual seja inicializado corretamente"""
        # Regras específicas para 'Declaração de compensação pagamento indevido'
        if self.metodo_credito == 'Declaração de compensação pagamento indevido':
            # Se ambos valores existem, calcula saldo como diferença
            if self.valor_do_principal is not None and self.total is not None:
                diferenca = self.valor_do_principal - self.total
                # Garante que não fique negativo
                if diferenca < 0:
                    # Evita persistir saldo negativo; força a zero
                    diferenca = 0
                self.saldo = diferenca
        # Se é um n8ovo objeto (não tem ID) e o saldo_atual não foi definido, inicializa com saldo calculado/fornecido
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

    def clean(self):
        from django.core.exceptions import ValidationError
        # Validação específica do método pagamento indevido
        if self.metodo_credito == 'Declaração de compensação pagamento indevido':
            if self.valor_do_principal is not None and self.total is not None:
                if self.total > self.valor_do_principal:
                    raise ValidationError({'total': 'O Total não pode ser maior que o Valor do Principal.'})
            # Exige ambos preenchidos
            if (self.valor_do_principal is None) or (self.total is None):
                raise ValidationError('Preencha Valor do Principal e Total para este método.')
    
    
    class Meta:
        verbose_name = 'Adesão'
        verbose_name_plural = 'Adesões'
    
