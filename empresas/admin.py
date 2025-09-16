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

	# Remover ação de exclusão em massa
	def get_actions(self, request):
		actions = super().get_actions(request)
		if 'delete_selected' in actions:
			del actions['delete_selected']
		return actions

	# Bloqueia permissão de exclusão
	def has_delete_permission(self, request, obj=None):
		return False

	# Esconde botão "Excluir" na página de alteração
	def change_view(self, request, object_id, form_url='', extra_context=None):
		extra_context = extra_context or {}
		extra_context['show_delete'] = False
		return super().change_view(request, object_id, form_url, extra_context=extra_context)

	# Bloqueia acesso à view de deleção direta (via URL)
	def delete_view(self, request, object_id, extra_context=None):
		from django.http import HttpResponseForbidden
		return HttpResponseForbidden("Exclusão de empresas não é permitida para manter a consistência dos dados.")


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

