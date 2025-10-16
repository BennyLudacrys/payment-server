"""
Configuração completa do Django para integração com frontend Vuex/Quasar.
"""

from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-m4+1vrysfm%p1xh&o008ki*aij2g=kqtmb01n@lxm9w7j_+!)@'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'corsheaders',
    
 
    'payments_mpesa',
    'payments_emola'
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gateway.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gateway.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('MYSQL_DB_NAME'),
        'USER': os.getenv('MYSQL_USER'),
        'PASSWORD': os.getenv('MYSQL_PASSWORD'),
        'HOST': os.getenv('MYSQL_HOST', 'localhost'),
        'PORT': os.getenv('MYSQL_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}

# Para desenvolvimento local, pode usar SQLite descomentando:
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


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


LANGUAGE_CODE = 'pt-br' 

TIME_ZONE = 'Africa/Maputo'  

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ==================== CONFIGURAÇÕES DE CORS ====================
# CRÍTICO: Sem isso, o frontend não conseguirá fazer requisições

# Origens permitidas (ajuste conforme necessário)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8080",      # Quasar dev padrão
    "http://localhost:9000",      # Quasar dev alternativo
    "http://127.0.0.1:8080",
    "http://127.0.0.1:9000",
    "https://mpesaemolatech.com",  # Produção
]

# Para desenvolvimento, pode permitir todas as origens (NÃO usar em produção)
# CORS_ALLOW_ALL_ORIGINS = True

# Headers permitidos
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Métodos HTTP permitidos
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Permitir cookies e credenciais
CORS_ALLOW_CREDENTIALS = True


# ==================== CONFIGURAÇÕES DE CSRF ====================
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8080",
    "http://localhost:9000",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:9000",
    "https://mpesaemolatech.com",
]


# ==================== CONFIGURAÇÕES DE LOGGING ====================
# Criar pasta logs se não existir
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {process:d} {thread:d} - {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file_mpesa': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'mpesa_transactions.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'file_errors': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'errors.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'payments_mpesa': {
            'handlers': ['console', 'file_mpesa', 'file_errors'],
            'level': 'INFO',
            'propagate': False,
        },
        'payments_emola': {
            'handlers': ['console', 'file_mpesa', 'file_errors'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console', 'file_errors'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}


# ==================== CONFIGURAÇÕES DO M-PESA ====================
MPESA_CONFIG = {
    'API_KEY': os.getenv('MPESA_API_KEY'),
    'PUBLIC_KEY': os.getenv('MPESA_PUBLIC_KEY'),
    'ENV': os.getenv('MPESA_ENV', 'sandbox'),
    'SERVICE_PROVIDER_CODE': os.getenv('MPESA_SERVICE_PROVIDER_CODE'),
    'THIRD_PARTY_REFERENCE': os.getenv('MPESA_THIRD_PARTY_REFERENCE', 'DEFAULT_REF_123'),
}


# ==================== CONFIGURAÇÕES DA EMOLA ====================
EMOLA_CONFIG = {
    'USERNAME': os.getenv('EMOLA_USERNAME'),
    'PASSWORD': os.getenv('EMOLA_PASSWORD'),
    'KEY': os.getenv('EMOLA_KEY'),
    'PARTNER_CODE': os.getenv('EMOLA_PARTNER_CODE'),
    'ENDPOINT': os.getenv('EMOLA_ENDPOINT', 'https://api.emola.com'),
}


# ==================== SEGURANÇA (para produção) ====================
if not DEBUG:
    # HTTPS
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # HSTS
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Outras configurações de segurança
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'