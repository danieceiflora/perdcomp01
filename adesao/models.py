from django.db import models
from clientes_parceiros.models import ClientesParceiros
from correcao.models import Correcao

class Adesao(models.Model):

    cliente_id = models.ForeignKey(
        ClientesParceiros,
        on_delete=models.CASCADE,
        related_name='adesao'
    ),

    correcao_id = models.ForeignKey(
        Correcao,
        on_delete=models.CASCADE,
        related_name='adesao'
    ),

    data_inicio = models.DateField(
        verbose_name='Data de Início',
        help_text='Data em que a adesão foi iniciada'
    ),
    perdcomp = models.CharField(
        max_length=30,
    ),

    saldo = models.FloatField(
        verbose_name='Saldo'
    ),
    
    free_rate = models.FloatField(
        verbose_name='Free Rate'),

    def __str__(self):
        return self.perdcomp
    
