from django.contrib import admin
from .models import Empresa, Socio, ParticipacaoSocietaria


class ParticipacaoInline(admin.TabularInline):
	model = ParticipacaoSocietaria
	extra = 1
	autocomplete_fields = ['socio']
	fields = ('socio', 'percentual', 'data_entrada', 'data_saida', 'ativo')


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
	list_display = ('razao_social', 'nome_fantasia', 'cnpj')
	search_fields = ('razao_social', 'nome_fantasia', 'cnpj')
	inlines = [ParticipacaoInline]


class ParticipacaoInlineForSocio(admin.TabularInline):
	model = ParticipacaoSocietaria
	extra = 1
	autocomplete_fields = ['empresa']
	fields = ('empresa', 'percentual', 'data_entrada', 'data_saida', 'ativo')


@admin.register(Socio)
class SocioAdmin(admin.ModelAdmin):
	list_display = ('nome', 'cpf', 'user', 'ativo')
	search_fields = ('nome', 'cpf', 'user__username')
	list_filter = ('ativo',)
	inlines = [ParticipacaoInlineForSocio]
	autocomplete_fields = ['user']


@admin.register(ParticipacaoSocietaria)
class ParticipacaoAdmin(admin.ModelAdmin):
	list_display = ('socio', 'empresa', 'percentual', 'ativo')
	list_filter = ('ativo', 'empresa')
	search_fields = ('socio__nome', 'socio__cpf', 'empresa__razao_social', 'empresa__nome_fantasia')
	autocomplete_fields = ['socio', 'empresa']

