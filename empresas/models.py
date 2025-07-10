from django.db import models

class Empresa(models.Model):
    cnpj = models.CharField("CNPJ", max_length=20, unique=True)
    razao_social = models.CharField("Razão Social", max_length=100)
    nome_fantasia = models.CharField("Nome Fantasia", max_length=100, blank=True)
    codigo_origem = models.CharField("Código de Origem", max_length=20, blank=True)
    logomarca = models.ImageField("Logomarca", upload_to='logomarcas/', blank=True, null=True)
    
    def __str__(self):
        return self.nome_fantasia or self.razao_social
