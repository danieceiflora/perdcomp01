from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
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

    perdcomp = models.CharField(
        max_length=100,
        verbose_name='PER/DCOMP da Declaração',
        help_text='Identificador da declaração de compensação que originou este lançamento.',
        blank=True,
        null=True,
        db_index=True,
    )

    item = models.CharField(
        max_length=10,
        verbose_name='Item da Declaração',
        help_text='Código do item do débito dentro da declaração de compensação.',
        blank=True,
        null=True,
    )
    
    data_lancamento = models.DateTimeField(
        verbose_name='Data do pedido',
        help_text='Data em que o pedido foi realizado'
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
    
    codigo_guia = models.CharField(
        max_length=60,
        verbose_name='Código da Guia',
        blank=True,
        null=True,
        help_text='Identificador da guia vinculada ao lançamento.'
    )

    saldo_restante = models.FloatField(
        verbose_name='Saldo Restante',
        help_text='Saldo da adesão após este lançamento',
        null=True,
        blank=True
    )

    data_credito = models.DateField(
        verbose_name='Data do Crédito',
        help_text='Data em que o crédito foi efetivado em conta',
        null=True,
        blank=True
    )

    valor_credito_em_conta = models.FloatField(
        verbose_name='Valor do Crédito em Conta',
        help_text='Valor creditado conforme notificação',
        null=True,
        blank=True
    )

    # Campos de aprovação
    aprovado = models.BooleanField(
        default=False,
        verbose_name='Aprovado'
    )
    data_aprovacao = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Data de Aprovação'
    )
    observacao_aprovacao = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observação da Aprovação'
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

    # Novos campos para débitos informados junto ao crédito (multi-itens)
    codigo_receita = models.CharField(
        max_length=20,
        verbose_name='Código da Receita (Débito)',
        blank=True,
        null=True
    )
    codigo_receita_denominacao = models.CharField(
        max_length=120,
        verbose_name='Código Receita / Denominação (Débito)',
        blank=True,
        null=True
    )
    periodo_apuracao_debito = models.CharField(
        max_length=20,
        verbose_name='Período de Apuração (Débito)',
        blank=True,
        null=True
    )

    def __str__(self):
        ref = self.perdcomp or self.id_adesao.perdcomp
        item_label = f"/{self.item}" if self.item else ''
        return f"{ref}{item_label} - {self.sinal}{self.valor} - {self.data_lancamento}"
        
    def clean(self):
        """
        Validação do modelo para garantir regras de negócio:
        - Lançamentos de débito não podem deixar o saldo negativo quando aprovados
        """
        from django.core.exceptions import ValidationError
        
        # Se estiver aprovando (ou já aprovado), valida saldo para débitos
        if self.aprovado and self.sinal == '-':
            adesao = self.id_adesao
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
        # Regras de aprovação: se não aprovado, não pode ter data; se aprovado sem data, define agora
        if not self.aprovado and self.data_aprovacao is not None:
            raise ValidationError({'data_aprovacao': 'Data de aprovação só pode existir quando o lançamento estiver aprovado.'})
            
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
        from django.core.exceptions import ValidationError
        from django.utils import timezone

        # Verifica se é um novo lançamento e captura estado anterior
        is_novo = not self.pk
        original_aprovado = False
        if not is_novo:
            try:
                original = type(self).objects.get(pk=self.pk)
                original_aprovado = bool(original.aprovado)
            except type(self).DoesNotExist:
                original_aprovado = False

        # Regras de aprovação antes de salvar: auto-definir/limpar data
        if self.aprovado and self.data_aprovacao is None:
            self.data_aprovacao = timezone.now()
        if not self.aprovado:
            self.data_aprovacao = None

        # Imutabilidade: após criação, apenas campos de aprovação podem mudar
        if not is_novo:
            allowed = {'aprovado', 'data_aprovacao', 'observacao_aprovacao'}
            changed = set()
            for field in self._meta.fields:
                fname = field.name
                if fname in ('id', 'pk', 'data_criacao'):
                    continue
                old_val = getattr(original, fname)
                new_val = getattr(self, fname)
                if old_val != new_val:
                    changed.add(fname)
            if changed - allowed:
                raise ValidationError('Após a criação, apenas os campos de aprovação podem ser editados.')
            # Bloquear mudança de status após aprovado
            if original_aprovado and self.aprovado is not True:
                raise ValidationError('Não é permitido alterar o status após aprovado.')

        with transaction.atomic():
            # Salva o lançamento
            super().save(*args, **kwargs)
            
            # Atualiza o saldo apenas quando aprovação ocorre
            should_update_saldo = False
            if is_novo and self.aprovado:
                should_update_saldo = True
            elif (not is_novo) and (not original_aprovado) and self.aprovado:
                should_update_saldo = True

            if should_update_saldo:
                # Validação final do saldo em caso de débito já foi feita em clean(); ainda assim garantir coerência
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

    class Meta:
        unique_together = (('perdcomp', 'item'),)

class Anexos(models.Model):
    id_lancamento = models.ForeignKey(
        Lancamentos,
        on_delete=models.CASCADE, 
        related_name='anexos',
        verbose_name='Lançamento'
    )
    
    def _anexo_upload_path(instance, filename):
        # Evita path traversal garantindo somente nome básico
        import os
        base = os.path.basename(filename)
        return f'documentos/lancamentos/{base}'

    def validar_tamanho(arquivo):
        max_mb = 10
        if arquivo.size > max_mb * 1024 * 1024:
            raise ValidationError(f"Arquivo excede {max_mb}MB.")

    arquivo = models.FileField(
        upload_to=_anexo_upload_path,
        verbose_name='Arquivo',
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf','jpg','jpeg','png','gif','txt','csv','xlsx','xls']),
            validar_tamanho
        ]
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

