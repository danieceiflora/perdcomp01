import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Garante a existência de um superusuário padrão em produção."

    def add_arguments(self, parser):
        parser.add_argument("--username", default=None, help="Username do superusuário.")
        parser.add_argument("--email", default=None, help="Email do superusuário.")
        parser.add_argument("--password", default=None, help="Senha do superusuário.")

    def handle(self, *args, **options):
        username = options["username"] or os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
        email = options["email"] or os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@gmail.com")
        password = options["password"] or os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin")

        if not password:
            raise ValueError("Senha do superusuário não pode ser vazia.")

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Superusuário '{username}' criado."))
            return

        updates = []
        if user.email != email:
            user.email = email
            updates.append("email")
        if not user.is_staff:
            user.is_staff = True
            updates.append("is_staff")
        if not user.is_superuser:
            user.is_superuser = True
            updates.append("is_superuser")
        if not user.check_password(password):
            user.set_password(password)
            updates.append("password")

        if updates:
            user.save()
            self.stdout.write(
                self.style.WARNING(
                    f"Superusuário '{username}' já existia; campos atualizados: {', '.join(updates)}."
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS(f"Superusuário '{username}' já estava configurado."))
