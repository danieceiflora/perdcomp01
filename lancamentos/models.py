from django.db import models
from adesao.models import Adesao
from django.urls import reverse
from datetime import datetime, timedelta
from simple_history.models import HistoricalRecords

class Lancamentos(models.Model):
    id_adesao = models.ForeignKey(
        Adesao,
        on_delete=models.PROTECT,
        related_name='lancamentos',
        verbose_name='Adesão'
    )
    
    data_lancamento = models.DateTimeField(
        verbose_name='Data do Lançamento',
        help_text='Data em que o lançamento foi realizado'
    )
    
    valor = models.FloatField(
        verbose_name='Valor do Lançamento',
        help_text='Valor do lançamento realizado',
        null=True,
        blank=True
    )
    
    sinal = models.CharField(
        max_length=1,
        choices=[
            ('+', 'Crédito'),
            ('-', 'Débito'),
        ],
    default='-',
        verbose_name='Sinal do Lançamento',
        help_text='Indica se o lançamento é um crédito ou débito'
    )
    
    tipo = models.CharField(
        max_length=20,
        choices=[
            ('Gerado', 'GERADO'),
            ('Correção', 'CORREÇÃO'),
            ('Originado no Ecac', 'ORIGINADO NO ECAC'),
        ],
        verbose_name='Tipo de Lançamento',
        blank=True, 
        null=True
    )
    
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Criação'
    )
    
    descricao = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observação'
    )
    
    saldo_restante = models.FloatField(
        verbose_name='Saldo Restante',
        help_text='Saldo da adesão após este lançamento',
        null=True,
        blank=True
    )

    # Campos adicionais para rastrear origem dos valores conforme método
    metodo = models.CharField(
        max_length=60,
        verbose_name='Método do Lançamento',
        blank=True,
        null=True,
        help_text='Pedido de ressarcimento, Pedido de restituição, etc.'
    )
    total = models.FloatField(
        verbose_name='Total (Ressarcimento / Compensação)',
        blank=True,
        null=True
    )
    total_credito_original_utilizado = models.FloatField(
        verbose_name='Total Crédito Original Utilizado (Restituição)',
        blank=True,
        null=True
    )
    periodo_apuracao = models.CharField(
        max_length=20,
        verbose_name='Período de Apuração',
        blank=True,
        null=True
    )
    periodo_apuracao_r = models.CharField(
        max_length=20,
        verbose_name='Período de Apuração (Ressarcimento)',
        blank=True,
        null=True
    )
    debito = models.FloatField(
        verbose_name='Débito (Restituição)',
        blank=True,
        null=True
    )
    debito_r = models.FloatField(
        verbose_name='Débito (Ressarcimento)',
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.id_adesao.perdcomp} - {self.sinal}{self.valor} - {self.data_lancamento}"
    
    def clean(self):
        """
        Validação do modelo para garantir regras de negócio:
        - Lançamentos de débito não podem deixar o saldo negativo
        """
        from django.core.exceptions import ValidationError
        
        # Se for um novo lançamento de débito, verifica se o saldo ficaria negativo
        if not self.pk and self.sinal == '-':
            adesao = self.id_adesao
            # Inicializa saldo_atual se estiver None
            if adesao.saldo_atual is None:
                adesao.saldo_atual = adesao.saldo or 0
            try:
                valor_numerico = float(self.valor or 0)
            except (TypeError, ValueError):
                raise ValidationError({'valor': 'Valor inválido.'})
            novo_saldo = (adesao.saldo_atual or 0) - valor_numerico
            if novo_saldo < 0:
                raise ValidationError({
                    'valor': f"O saldo não pode ficar negativo. Saldo atual: R$ {adesao.saldo_atual}, Valor do débito: R$ {valor_numerico}"
                })
            
    def pode_editar_anexos(self):
        """
        Verifica se os anexos do lançamento podem ser editados.
        Os anexos sempre podem ser editados.
        """
        return True
        
    def get_absolute_url(self):
        return reverse('lancamentos:detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para gerenciar a atualização do saldo
        sempre que um novo lançamento for adicionado.
        """
        from django.db import transaction
        
        # Verifica se é um novo lançamento
        is_novo = not self.pk
        
        with transaction.atomic():
            # Salva o lançamento
            super().save(*args, **kwargs)
            
            # Atualiza o saldo apenas para novos lançamentos
            if is_novo:
                self.atualizar_saldo_adesao()
                
        return self
    
    def atualizar_saldo_adesao(self):
        """
        Atualiza o saldo atual da adesão com base no valor e sinal deste lançamento.
        Também registra o saldo restante no próprio lançamento para referência histórica.
        Esta função deve ser chamada dentro de um bloco de transação para garantir a atomicidade.
        """
        adesao = self.id_adesao
        if adesao.saldo_atual is None:
            adesao.saldo_atual = adesao.saldo or 0
        try:
            valor_numerico = float(self.valor or 0)
        except (TypeError, ValueError):
            valor_numerico = 0
        # Atualiza o saldo conforme o sinal do lançamento (protegendo negativo em débito)
        if self.sinal == '-':
            novo = adesao.saldo_atual - valor_numerico
            adesao.saldo_atual = novo if novo >= 0 else 0
        else:
            adesao.saldo_atual = (adesao.saldo_atual or 0) + valor_numerico
        
        # Registra o saldo restante no lançamento (registro histórico)
        self.saldo_restante = adesao.saldo_atual
        Lancamentos.objects.filter(pk=self.pk).update(saldo_restante=self.saldo_restante)
            
        # Salva a adesão com o novo saldo
        adesao.save(update_fields=['saldo_atual'])

    # Audit trail
    historico = HistoricalRecords()

class Anexos(models.Model):
    id_lancamento = models.ForeignKey(
        Lancamentos,
        on_delete=models.CASCADE, 
        related_name='anexos',
        verbose_name='Lançamento'
    )
    
    arquivo = models.FileField(
        upload_to='documentos/lancamentos/',
        verbose_name='Arquivo'
    )
    
    nome_anexo = models.CharField(
        max_length=100,
        verbose_name='Nome do anexo',
        blank=True,
        null=True
    )
    
    descricao = models.CharField(
        max_length=200,
        verbose_name='Descrição do conteúdo',
        blank=True,
        null=True
    )
    
    data_upload = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Upload'
    )

    # Audit trail
    historico = HistoricalRecords()
    
    def __str__(self):
        return self.nome_anexo or f"Anexo {self.id}" or "Anexo sem nome"

