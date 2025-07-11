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
