from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from utils.validators import validate_cnpj

class Empresa(models.Model):
    cnpj = models.CharField("CNPJ", max_length=20, unique=True, validators=[validate_cnpj])
    razao_social = models.CharField("Razão Social", max_length=100)
    nome_fantasia = models.CharField("Nome Fantasia", max_length=100, blank=True)
    codigo_origem = models.CharField("Código de Origem", max_length=20, blank=True)
    def _logo_upload_path(instance, filename):
        import os
        base = os.path.basename(filename)
        return f'logomarcas/{base}'

    def validar_logo_tamanho(arquivo):
        max_mb = 5
        if arquivo and hasattr(arquivo, 'size') and arquivo.size > max_mb * 1024 * 1024:
            raise ValidationError(f"Logomarca excede {max_mb}MB.")

    logomarca = models.ImageField(
        "Logomarca",
        upload_to=_logo_upload_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['jpg','jpeg','png','gif']), validar_logo_tamanho]
    )
    
    def __str__(self):
        return self.nome_fantasia or self.razao_social
