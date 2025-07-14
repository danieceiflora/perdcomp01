from django.db import models
from adesao.models import Adesao
from django.urls import reverse
from datetime import datetime, timedelta

class Lancamentos(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('CONFIRMADO', 'Confirmado'),
        ('ESTORNADO', 'Estornado'),
    ]
    
    id_adesao = models.ForeignKey(
        Adesao,
        on_delete=models.PROTECT,
        related_name='lancamentos',
        verbose_name='Adesão'
    )
    
    data_lancamento = models.DateField(
        verbose_name='Data do Lançamento',
        help_text='Data em que o lançamento foi realizado'
    )
    
    valor = models.FloatField(
        verbose_name='Valor do Lançamento',
        help_text='Valor do lançamento realizado'
    )
    
    sinal = models.CharField(
        max_length=1,
        choices=[
            ('+', 'Crédito'),
            ('-', 'Débito'),
        ],
        default='+',
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
    
    observacao = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observação'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDENTE',
        verbose_name='Status do Lançamento'
    )
    
    lancamento_original = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='lancamentos_estorno',
        verbose_name='Lançamento Original'
    )
    
    data_confirmacao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data de Confirmação'
    )

    def __str__(self):
        return f"{self.id_adesao.perdcomp} - {self.sinal}{self.valor} - {self.data_lancamento}"
    
    def pode_editar(self):
        """
        Verifica se o lançamento ainda pode ser editado.
        Um lançamento só pode ser editado se estiver no status PENDENTE.
        """
        if self.status != 'PENDENTE':
            return False
            
        return True
        
    def pode_excluir(self):
        """
        Verifica se o lançamento pode ser excluído.
        Um lançamento só pode ser excluído se estiver no status PENDENTE.
        """
        return self.status == 'PENDENTE'
    
    def pode_editar_anexos(self):
        """
        Verifica se os anexos do lançamento podem ser editados.
        Os anexos podem ser editados independentemente do status do lançamento.
        """
        return True
        
    def get_absolute_url(self):
        return reverse('lancamentos:detail', kwargs={'pk': self.pk})

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
        verbose_name='Nome do anexo'
    )
    
    descricao = models.CharField(
        max_length=200,
        verbose_name='Descrição do conteúdo'
    )
    
    data_upload = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Upload'
    )
    
    def __str__(self):
        return self.nome_anexo

