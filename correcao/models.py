from django.db import models

class Correcao(models.Model):
    descricao = models.CharField(max_length=50)
    fonte_correcao = models.CharField(max_length=200)
    cod_origem = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.descricao
    
    class Meta:
        verbose_name = 'Correção'
        verbose_name_plural = 'Correções'

class tipoTese(models.Model):
    descricao = models.CharField(max_length=50, verbose_name='Categoria')
    def __str__(self):
        return self.descricao
    
class TeseCredito(models.Model):
    id_correcao = models.ForeignKey(Correcao, on_delete=models.PROTECT, verbose_name='Índice de Correção', blank=True, null=True)
    id_tipo_tese = models.ForeignKey(tipoTese, on_delete=models.PROTECT, verbose_name='Tipo de Tese')
    descricao = models.CharField(max_length=50)
    jurisprudencia = models.CharField(max_length=200)
    corrige = models.BooleanField(default=False, null=True, blank=True)
    cod_origem = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.descricao


