from django.contrib import admin
from empresas.models import Empresa

class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('cnpj', 'razao_social', 'nome_fantasia', 'codigo_origem')
    search_fields = ('cnpj', 'razao_social', 'nome_fantasia')
admin.site.register(Empresa, EmpresaAdmin)