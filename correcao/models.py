from django.db import models
from simple_history.models import HistoricalRecords


class Correcao(models.Model):
    descricao = models.CharField(max_length=50)
    fonte_correcao = models.CharField(max_length=200)
    cod_origem = models.CharField(max_length=20, blank=True, null=True)
    historico = HistoricalRecords()

    def __str__(self):
        return self.descricao
    
    class Meta:
        verbose_name = 'Correção'
        verbose_name_plural = 'Correções'

class tipoTese(models.Model):
    descricao = models.CharField(max_length=50, verbose_name='Categoria')
    periodicidade_options = [
        ('semanal', 'Semanal'),
        ('mensal', 'Mensal'),
        ('anual', 'Anual'),
        ('trimestral', 'Trimestral'),
        ('semestral', 'Semestral'),
    ]
    periodicidade = models.CharField(
        max_length=20,
        choices=periodicidade_options,
        default='mensal',
        verbose_name='Periodicidade'
    )
    historico = HistoricalRecords()
    def __str__(self):
        return self.descricao
    class Meta:
        verbose_name = 'Tipo de documento'
        verbose_name_plural = 'Tipos de documentos'
    
class TeseCredito(models.Model):
    id_correcao = models.ForeignKey(Correcao, on_delete=models.PROTECT, verbose_name='Índice de Correção', blank=True, null=True)
    id_tipo_tese = models.ForeignKey(tipoTese, on_delete=models.PROTECT, verbose_name='Tipo de documento')
    descricao = models.CharField(max_length=50)
    jurisprudencia = models.CharField(max_length=200)
    corrige = models.BooleanField(default=False, null=True, blank=True)
    cod_origem = models.CharField(max_length=20, blank=True, null=True)
    historico = HistoricalRecords()

    class Meta:
        verbose_name = 'Forma de Habilitação'
        verbose_name_plural = 'Formas de Habilitações'

    def __str__(self):
        return self.descricao


