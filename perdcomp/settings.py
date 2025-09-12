
from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-5zmof9y39ed%%3!%#vsc7ur#5pr8gi$#)#-!mrp&ts0x+=%398')  # TODO: definir via variável de ambiente em produção

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() in ('1','true','yes')

ALLOWED_HOSTS = [h.strip() for h in os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',') if h.strip()]

# Configurações CSRF para funcionar com Nginx
CSRF_TRUSTED_ORIGINS = [
    'http://localhost',
    'http://127.0.0.1',
    'http://177.153.62.100:3000',
    'https://programmer-ribbon-ellis-raid.trycloudflare.com',
    'https://tvs-dentists-festival-usb.trycloudflare.com',
]

# Configurações adicionais para CSRF com proxy
CSRF_USE_SESSIONS = False
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = False  # Manter False até termos HTTPS
CSRF_COOKIE_NAME = 'csrftoken'

# Opcional: permitir definir origens CSRF adicionais via variável
_extra_csrf = os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS')
if _extra_csrf:
    CSRF_TRUSTED_ORIGINS = list(set(CSRF_TRUSTED_ORIGINS + [o.strip() for o in _extra_csrf.split(',') if o.strip()]))

# Application definition

INSTALLED_APPS = [  # Tema customizado para o admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'clientes_parceiros',
    'empresas',
    'contatos',
    'correcao',
    'adesao',
    'lancamentos',
    'dashboard',
    'rest_framework',
    'drf_spectacular',
    'utils',
    'simple_history'  # App utilitário (filtros de template, etc.)
]
# Adicionando configuração do JWT
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'PERDCOMP API',
    'DESCRIPTION': 'Documentação interativa da API PERDCOMP',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'CONTACT': {'name': 'Equipe PERDCOMP', 'email': 'suporte@example.com'},
    'LICENSE': {'name': 'Proprietary'},
    'SERVERS': [
        {'url': 'http://localhost:8000', 'description': 'Local'},
    ],
}

MIDDLEWARE = [
    'simple_history.middleware.HistoryRequestMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # Adiciona WhiteNoise (se instalado) para servir estáticos de forma segura em produção
    # 'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # Middleware para tradução
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'perdcomp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['perdcomp/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'perdcomp.wsgi.application'


# Database
# Em desenvolvimento, usamos SQLite (padrão). Em produção, defina DJANGO_DB_ENGINE=postgres
# e variáveis POSTGRES_* para usar Postgres.
SQLITE_PATH = os.getenv('DJANGO_SQLITE_PATH', str(BASE_DIR / 'db.sqlite3'))

DB_ENGINE = os.getenv('DJANGO_DB_ENGINE', '').lower()
if DB_ENGINE in ('postgres', 'postgresql', 'pgsql', 'psql'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', 'perdcomp'),
            'USER': os.getenv('POSTGRES_USER', 'perdcomp'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'perdcomp'),
            'HOST': os.getenv('POSTGRES_HOST', 'postgres'),
            'PORT': os.getenv('POSTGRES_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': SQLITE_PATH,
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Configurações de localização
LANGUAGES = [
    ('pt-br', 'Português')
]

# Diretório para arquivos de tradução (se necessário criar traduções customizadas)
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'

# Configuração de estáticos para produção
STATICFILES_DIRS = [
    BASE_DIR / 'perdcomp' / 'static',
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Arquivos de mídia(uploads)

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ======= Segurança adicional (apenas se DEBUG False) =======
if not DEBUG:
    SESSION_COOKIE_SECURE = False  # Manter False até HTTPS
    # CSRF_COOKIE_SECURE = True  # Comentado até termos HTTPS
    SECURE_SSL_REDIRECT = os.getenv('DJANGO_SECURE_SSL_REDIRECT', 'False').lower() in ('1','true','yes')  # Default False
    SECURE_HSTS_SECONDS = int(os.getenv('DJANGO_SECURE_HSTS_SECONDS', '0'))  # Desabilitado até HTTPS
    # SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # Comentado até HTTPS
    # SECURE_HSTS_PRELOAD = True  # Comentado até HTTPS
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    SECURE_BROWSER_XSS_FILTER = True  # (obsoleto em alguns navegadores, mantido por compat.)
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    # Content Security Policy básica (se usar django-csp instalar e ajustar)
    # Exemplo de variável: os.environ.get('CSP_DEFAULT_SRC', "'self'")

    # Proxy headers (quando atrás de Nginx/Load Balancer)
    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# WhiteNoise opcional (habilitar via var DJANGO_ENABLE_WHITENOISE=1)
if os.getenv('DJANGO_ENABLE_WHITENOISE', '0').lower() in ('1','true','yes') and 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
