from django.db import models

class Correcao(models.Model):
    cod_origem = models.CharField(max_length=20)
    descricao = models.CharField(max_length=50)
    fonte_correcao = models.CharField(max_length=200)

    def __str__(self):
        return self.descricao
    
    class Meta:
        verbose_name = 'Correção'
        verbose_name_plural = 'Correções'

class tipoTese(models.Model):
    descricao = models.CharField(max_length=50)
    def __str__(self):
        return self.descricao
    
class TeseCredito(models.Model):
    id_correcao = models.ForeignKey(Correcao, on_delete=models.CASCADE)
    id_tipo_tese = models.ForeignKey(tipoTese, on_delete=models.CASCADE)
    cod_origem = models.CharField(max_length=20)
    descricao = models.CharField(max_length=50)
    jurisprudencia = models.CharField(max_length=200)
    corrige = models.BooleanField(default=False)
    correcao = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.descricao


