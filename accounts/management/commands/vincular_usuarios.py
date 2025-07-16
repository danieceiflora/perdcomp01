from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from accounts.models import UserProfile
from clientes_parceiros.models import ClientesParceiros
from empresas.models import Empresa

class Command(BaseCommand):
    help = 'Vincula usuários existentes a relacionamentos de ClientesParceiros'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Nome de usuário específico para vincular',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Listar todos os usuários sem perfil',
        )
        parser.add_argument(
            '--create-profile',
            action='store_true',
            help='Criar perfil para usuário interativamente',
        )
    
    def handle(self, *args, **options):
        if options['all']:
            self.listar_usuarios_sem_perfil()
        elif options['username'] and options['create_profile']:
            self.criar_perfil_interativo(options['username'])
        elif options['username']:
            self.mostrar_usuario(options['username'])
        else:
            self.mostrar_ajuda()
    
    def listar_usuarios_sem_perfil(self):
        """Lista usuários que não possuem perfil"""
        usuarios_sem_perfil = User.objects.filter(profile__isnull=True)
        
        if not usuarios_sem_perfil.exists():
            self.stdout.write(
                self.style.SUCCESS('Todos os usuários já possuem perfil!')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(f'Encontrados {usuarios_sem_perfil.count()} usuários sem perfil:')
        )
        
        for user in usuarios_sem_perfil:
            self.stdout.write(f"  - {user.username} ({user.get_full_name() or 'Sem nome'}) - {user.email or 'Sem email'}")
        
        self.stdout.write('\nUse: python manage.py vincular_usuarios --username <username> --create-profile')
    
    def mostrar_usuario(self, username):
        """Mostra informações de um usuário específico"""
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'Usuário "{username}" não encontrado.')
        
        self.stdout.write(f'\nInformações do usuário: {username}')
        self.stdout.write(f'Nome completo: {user.get_full_name() or "Não informado"}')
        self.stdout.write(f'Email: {user.email or "Não informado"}')
        self.stdout.write(f'Ativo: {"Sim" if user.is_active else "Não"}')
        self.stdout.write(f'Staff: {"Sim" if user.is_staff else "Não"}')
        
        try:
            profile = user.profile
            self.stdout.write(f'\nPerfil encontrado:')
            self.stdout.write(f'Relacionamento: {profile.relacionamento}')
            self.stdout.write(f'Empresa Base: {profile.empresa_base}')
            self.stdout.write(f'Empresa Vinculada: {profile.empresa_vinculada}')
            self.stdout.write(f'Tipo: {profile.tipo_relacionamento}')
            self.stdout.write(f'Telefone: {profile.telefone or "Não informado"}')
            self.stdout.write(f'Ativo: {"Sim" if profile.ativo else "Não"}')
        except UserProfile.DoesNotExist:
            self.stdout.write(
                self.style.WARNING('\nEste usuário não possui perfil!')
            )
            self.stdout.write('Use: python manage.py vincular_usuarios --username {} --create-profile'.format(username))
    
    def criar_perfil_interativo(self, username):
        """Cria um perfil para o usuário de forma interativa"""
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'Usuário "{username}" não encontrado.')
        
        # Verificar se já tem perfil
        if hasattr(user, 'profile'):
            raise CommandError(f'Usuário "{username}" já possui perfil!')
        
        self.stdout.write(f'\nCriando perfil para: {user.username} ({user.get_full_name() or "Sem nome"})')
        
        # Listar relacionamentos disponíveis
        relacionamentos = ClientesParceiros.objects.select_related(
            'id_company_base', 'id_company_vinculada', 'id_tipo_relacionamento'
        ).all()
        
        if not relacionamentos.exists():
            raise CommandError(
                'Nenhum relacionamento encontrado! '
                'Primeiro crie relacionamentos em ClientesParceiros.'
            )
        
        self.stdout.write('\nRelacionamentos disponíveis:')
        for i, rel in enumerate(relacionamentos, 1):
            self.stdout.write(
                f'{i:2d}. {rel.id_company_base.nome_fantasia or rel.id_company_base.razao_social} '
                f'-> {rel.id_company_vinculada.nome_fantasia or rel.id_company_vinculada.razao_social} '
                f'({rel.id_tipo_relacionamento.tipo_relacionamento})'
            )
        
        # Solicitar escolha
        while True:
            try:
                escolha = input('\nEscolha um relacionamento (número): ')
                indice = int(escolha) - 1
                if 0 <= indice < len(relacionamentos):
                    relacionamento_escolhido = relacionamentos[indice]
                    break
                else:
                    self.stdout.write(self.style.ERROR('Número inválido!'))
            except (ValueError, KeyboardInterrupt):
                self.stdout.write(self.style.ERROR('\nOperação cancelada.'))
                return
        
        # Solicitar telefone (opcional)
        telefone = input('Telefone (opcional): ').strip()
        
        # Criar o perfil
        try:
            profile = UserProfile.objects.create(
                user=user,
                relacionamento=relacionamento_escolhido,
                telefone=telefone
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'\nPerfil criado com sucesso para {user.username}!')
            )
            self.stdout.write(f'Relacionamento: {profile.relacionamento}')
            self.stdout.write(f'Tipo de acesso: {profile.tipo_relacionamento}')
            self.stdout.write(f'Empresa base: {profile.empresa_base}')
            self.stdout.write(f'Empresa vinculada: {profile.empresa_vinculada}')
            
        except Exception as e:
            raise CommandError(f'Erro ao criar perfil: {e}')
    
    def mostrar_ajuda(self):
        """Mostra opções de uso do comando"""
        self.stdout.write('Uso do comando vincular_usuarios:')
        self.stdout.write('')
        self.stdout.write('  Listar usuários sem perfil:')
        self.stdout.write('    python manage.py vincular_usuarios --all')
        self.stdout.write('')
        self.stdout.write('  Ver informações de um usuário:')
        self.stdout.write('    python manage.py vincular_usuarios --username <username>')
        self.stdout.write('')
        self.stdout.write('  Criar perfil para um usuário:')
        self.stdout.write('    python manage.py vincular_usuarios --username <username> --create-profile')
