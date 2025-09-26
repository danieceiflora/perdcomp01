from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver
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


class Socio(models.Model):
    nome = models.CharField("Nome", max_length=120)
    cpf = models.CharField("CPF", max_length=14, unique=True, help_text="Somente dígitos ou formatado; será armazenado apenas com dígitos.")
    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name="Usuário", on_delete=models.SET_NULL, null=True, blank=True, related_name="socio")
    ativo = models.BooleanField("Ativo", default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sócio"
        verbose_name_plural = "Sócios"

    def __str__(self):
        return f"{self.nome} ({self.cpf})"


class ParticipacaoSocietaria(models.Model):
    empresa = models.ForeignKey(Empresa, verbose_name="Empresa", on_delete=models.CASCADE, related_name="participacoes")
    socio = models.ForeignKey(Socio, verbose_name="Sócio", on_delete=models.CASCADE, related_name="participacoes")
    percentual = models.DecimalField("Percentual", max_digits=5, decimal_places=2, null=True, blank=True, help_text="Percentual de participação (opcional)")
    data_entrada = models.DateField("Data de Entrada", null=True, blank=True)
    data_saida = models.DateField("Data de Saída", null=True, blank=True)
    ativo = models.BooleanField("Ativo", default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Participação Societária"
        verbose_name_plural = "Participações Societárias"
        unique_together = ("empresa", "socio")

    def __str__(self):
        return f"{self.socio} -> {self.empresa}"

    def is_vigente(self):
        from datetime import date
        hoje = date.today()
        if self.data_entrada and self.data_entrada > hoje:
            return False
        if self.data_saida and self.data_saida < hoje:
            return False
        return self.ativo


@receiver(pre_save, sender=Socio)
def normalizar_cpf(sender, instance, **kwargs):
    if instance.cpf:
        somente_digitos = ''.join(ch for ch in instance.cpf if ch.isdigit())
        instance.cpf = somente_digitos


# Sanitização de campos de Empresa antes de salvar
@receiver(pre_save, sender=Empresa)
def sanitizar_empresa(sender, instance, **kwargs):
    import re
    # Normaliza CNPJ removendo tudo que não seja letra ou número (validador já confere)
    if instance.cnpj:
        instance.cnpj = ''.join(re.findall(r'[0-9A-Za-z]', instance.cnpj)).upper()

    def limpar_texto(valor: str) -> str:
        if not valor:
            return valor
        # Remove caracteres de controle
        valor = ''.join(ch for ch in valor if ch.isprintable())
        # Substitui múltiplos espaços por um
        valor = re.sub(r'\s+', ' ', valor)
        # Remove caracteres especiais indesejados (mantém letras, números, espaço, pontuação básica)
        # Aqui decidimos permitir . , - _ / & ()
        valor = re.sub(r'[^0-9A-Za-zÁÂÃÀÄáâãàäÉÊÈéêèÍÎÌíîìÓÔÕÒÖóôõòöÚÛÙÜúûùüÇç .,_/&()\-]', '', valor)
        return valor.strip()

    instance.razao_social = limpar_texto(instance.razao_social)
    instance.nome_fantasia = limpar_texto(instance.nome_fantasia)
    instance.codigo_origem = limpar_texto(instance.codigo_origem)
