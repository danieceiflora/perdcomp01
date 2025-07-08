from django.db import models
from empresas.models import Empresa

class TipoContato(models.Model):
  tipo_contato_options = (
    ('Comercial', 'Comercial'),
    ('Celular', 'Celular'),
    ('Pessoal', 'Pessoal')
  )

  tipo_contato = models.CharField(choices=tipo_contato_options, max_length=50, default='Comercial')
  descricao = models.CharField(max_length=100)

class Contatos(models.Model):
  tipo_contato = models.ForeignKey(TipoContato, on_delete=models.CASCADE)
  empresa_base = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='empresa_base_contato')
  empresa_vinculada = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='empresa_vinculada_contato')
  telefone = models.CharField(max_length=20)
  email = models.EmailField(max_length=100)
  site = models.CharField(max_length=100)

  def __str__(self):
    return f"{self.tipo_contato} - {self.empresa_base} - {self.empresa_vinculada} - {self.telefone}"