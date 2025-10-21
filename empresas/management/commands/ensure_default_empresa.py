import os
from django.core.management.base import BaseCommand, CommandError

from empresas.models import Empresa


class Command(BaseCommand):
    help = (
        "Garantir que a empresa base exigida para vínculos esteja presente. "
        "Utilize as opções --cnpj e --razao para personalizar, ou variáveis de ambiente "
        "DEFAULT_EMPRESA_CNPJ/DEFAULT_EMPRESA_RAZAO/DEFAULT_EMPRESA_FANTASIA."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--cnpj",
            default=os.environ.get("DEFAULT_EMPRESA_CNPJ", "42994794000104"),
            help="CNPJ da empresa base (padrão: 42994794000104)",
        )
        parser.add_argument(
            "--razao",
            default=os.environ.get("DEFAULT_EMPRESA_RAZAO", "Axxen"),
            help="Razão social da empresa base (padrão: Axxen)",
        )
        parser.add_argument(
            "--fantasia",
            default=os.environ.get("DEFAULT_EMPRESA_FANTASIA", "Axxen"),
            help="Nome fantasia da empresa base (opcional)",
        )
        parser.add_argument(
            "--codigo-origem",
            default=os.environ.get("DEFAULT_EMPRESA_CODIGO_ORIGEM", ""),
            help="Código de origem cadastral (opcional)",
        )

    def handle(self, *args, **options):
        cnpj = (options.get("cnpj") or "").strip()
        razao = (options.get("razao") or "").strip()
        fantasia = (options.get("fantasia") or "").strip()
        codigo_origem = options.get("codigo-origem")

        if not cnpj:
            raise CommandError("Informe um CNPJ válido para a empresa base.")
        if not razao:
            raise CommandError("Informe uma razão social para a empresa base.")

        defaults = {
            "razao_social": razao,
            "nome_fantasia": fantasia or razao,
        }
        if codigo_origem is not None:
            defaults["codigo_origem"] = codigo_origem.strip()

        obj, created = Empresa.objects.update_or_create(cnpj=cnpj, defaults=defaults)

        action = "criada" if created else "atualizada"
        self.stdout.write(
            self.style.SUCCESS(
                f"Empresa base '{obj}' ({obj.cnpj}) {action} com sucesso."
            )
        )
