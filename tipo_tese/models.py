from django.db import models

class TipoTese(models.Model):
    descricao = models.CharField(max_length=20)

    def __str__(self):
        return self.descricao
    
    class Meta:
        verbose_name = 'Tipo de Tese'
        verbose_name_plural = 'Tipos de Tese'
