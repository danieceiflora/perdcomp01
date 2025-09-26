import os
import django

# Carrega as configurações do Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "perdcomp.settings")
django.setup()

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from django.utils.translation import gettext_lazy as _

print("Iniciando a atualização de nomes de permissões...")

# Mapeamento de ações para português
action_map = {
    "add": _("adicionar"),
    "change": _("alterar"),
    "delete": _("excluir"),
    "view": _("visualizar"),
}

# Itera sobre todos os modelos registrados no Django
for model in apps.get_models():
    # Ignora modelos que não devem ter permissões
    if not model._meta.managed or model._meta.proxy:
        continue

    try:
        ct = ContentType.objects.get_for_model(model, for_concrete_model=False)
    except ContentType.DoesNotExist:
        print(f"Aviso: ContentType não encontrado para o modelo {model._meta.model_name}, pulando.")
        continue

    # Determina o nome base para a permissão
    model_name_pt = model._meta.verbose_name
    
    # Caso especial para modelos de histórico (django-simple-history)
    if model._meta.model_name.startswith("historical"):
        # Tenta obter o nome do modelo original
        try:
            original_model_name = model.history_of.model._meta.verbose_name
            model_name_pt = f"histórico de {original_model_name}"
        except AttributeError:
            # Fallback se não conseguir encontrar o modelo original
            model_name_pt = f"histórico {model_name_pt}"

    # Itera sobre as ações (add, change, etc.)
    for action_en, action_pt in action_map.items():
        codename = f"{action_en}_{model._meta.model_name}"
        
        try:
            perm = Permission.objects.get(content_type=ct, codename=codename)
            
            # Monta o novo nome esperado em português
            novo_nome = f"Pode {action_pt} {model_name_pt}"
            
            # Atualiza apenas se o nome for diferente
            if perm.name != novo_nome:
                print(f'Renomeando: "{perm.name}" -> "{novo_nome}"')
                perm.name = novo_nome
                perm.save()

        except Permission.DoesNotExist:
            # A permissão (ex: 'view') pode não existir para todos os modelos
            continue

print("Atualização de permissões concluída.")