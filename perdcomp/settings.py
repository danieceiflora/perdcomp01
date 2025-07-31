
from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-5zmof9y39ed%%3!%#vsc7ur#5pr8gi$#)#-!mrp&ts0x+=%398'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'jazzmin',
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
]
# Adicionando configuração do JWT
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
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
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'perdcomp/static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Arquivos de mídia(uploads)

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

JAZZMIN_SETTINGS = {
    "site_title": "PERDCOMP Admin",
    "site_header": "PERDCOMP Administration",
    "site_brand": "PERDCOMP",
    "welcome_sign": "Bem-vindo ao painel de administração do PERDCOMP",
    "usermenu_links": [
        {
            "name": "Token JWT",
            "url": "token-jwt",
            "new_window": True,
            "icon": "fas fa-key",
        },
    ],
    "icons":
        {
            "clientes_parceiros.ClientesParceiros": "fas fa-users",
            "clientes_parceiros.TipoRelacionamento": "fa-solid fa-tag",
            "empresas.Empresa": "fas fa-building",
            "contatos.Contatos": "fas fa-address-book",
            "correcao.TeseCredito": "fas fa-balance-scale",
            "correcao.TipoTese": "fa-solid fa-tag",
            "adesao.Adesao": "fas fa-handshake",
            "lancamentos.Lancamentos": "fas fa-file-invoice-dollar",
            "correcao.Correcao": "fas fa-tools",
            "auth.User": "fas fa-user",
            "auth.Group": "fas fa-users-cog",
            "accounts.UserProfile": "fas fa-user-cog",
            "lancamentos.Anexos": "fas fa-paperclip",
        },
    "changeform_format": "single",  # <- Exibe tudo junto, sem abas nem colapsáveis
    "changeform_format_overrides": {
        "auth.user": "single",  # <- Garante isso no admin do User também
        "auth.group": "single",  # (opcional)
    },
    "show_ui_builder": True  # <- Desativa o construtor de UI
    
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-teal",
    "accent": "accent-teal",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": False,
    "sidebar": "sidebar-dark-teal",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "spacelab",
    "dark_mode_theme": "darkly",
    "button_classes": {
        "primary": "btn-outline-primary",
        "secondary": "btn-outline-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}