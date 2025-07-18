from django.db import models
from empresas.models import Empresa

class Contatos(models.Model):
  tipo_contato_options = (
    ('Comercial', 'Comercial'),
    ('Celular', 'Celular'),
    ('Pessoal', 'Pessoal')
  )
  tipo_contato = models.CharField(max_length=20, choices=tipo_contato_options, default='Comercial')
  empresa_base = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='empresa_base_contato')
  telefone = models.CharField(max_length=20)
  email = models.EmailField(max_length=100)
  site = models.CharField(max_length=100)

  class Meta:
    verbose_name = 'Contato'
    verbose_name_plural = 'Contatos'

  def __str__(self):
    return f"{self.tipo_contato} - {self.empresa_base} - {self.telefone}"