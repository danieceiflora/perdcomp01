from django.db import models
from simple_history.models import HistoricalRecords

    
class TeseCredito(models.Model):
    descricao = models.CharField(max_length=50)
    jurisprudencia = models.CharField(max_length=200)
    cod_origem = models.CharField(max_length=20, blank=True, null=True)
    historico = HistoricalRecords()

    class Meta:
        verbose_name = 'Forma de Habilitação'
        verbose_name_plural = 'Formas de Habilitações'

    def __str__(self):
        return self.descricao


