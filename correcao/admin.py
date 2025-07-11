from django.contrib import admin
from .models import Correcao

@admin.register(Correcao)
class CorrecaoAdmin(admin.ModelAdmin):
    list_display = ('cod_origem', 'descricao', 'fonte_correcao')
    list_filter = ('cod_origem',)
    search_fields = ('cod_origem', 'descricao', 'fonte_correcao')
    ordering = ('descricao',)
