"""
Django settings for jobcore project.

Generated by 'django-admin startproject' using Django 2.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
import datetime
import dotenv
import dj_database_url

# import django_heroku

dotenv.read_dotenv()

# django_heroku.settings(locals())

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')
# SECURITY WARNING: don't run with debug turned on in production!
_ENV_DEBUG = os.environ.get('DEBUG')
DEBUG = (_ENV_DEBUG == 'TRUE' or _ENV_DEBUG == 'True')
# DEBUG = (_ENV_DEBUG == 'FALSE' or _ENV_DEBUG == 'false')
ENVIRONMENT = os.environ.get('ENVIRONMENT')
DATABASE_URL = os.environ.get('DATABASE_URL')

ROLLBAR_POST_ACCESS_TOKEN = os.environ.get('ROLLBAR_POST_ACCESS_TOKEN')

# TODO: Remember deleting unused hosts in production
ALLOWED_HOSTS = [
    '*'
    # 'https://8000-lavender-alligator-jdqsikyc39p.ws-us34.gitpod.io'
]

# Application definition

INSTALLED_APPS = [
    'admin_tools',
    'admin_tools.theming',
    'admin_tools.menu',
    'admin_tools.dashboard',
    'whitenoise.runserver_nostatic',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'rest_framework',
    'oauth2_provider',
    'corsheaders',
    'api',
    'cloudinary'
]

LOGIN_URL = '/admin'
LOGOUT_URL = '/admin/logout'

AUTHENTICATION_BACKENDS = (
    'oauth2_provider.backends.OAuth2Backend',
    # Uncomment following if you want to access the admin
    'django.contrib.auth.backends.ModelBackend'
)

ROLLBAR = {
    'access_token': ROLLBAR_POST_ACCESS_TOKEN,
    'environment': ENVIRONMENT,
    'branch': 'master',
    'root': os.getcwd(),
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'api.utils.middleware.ValueErrorMiddleware',
]

if ENVIRONMENT == 'production':
    MIDDLEWARE.extend([
        'rollbar.contrib.django.middleware.RollbarNotifierMiddleware'
    ])

ROOT_URLCONF = 'jobcore.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                # insert your TEMPLATE_LOADERS here
                'admin_tools.template_loaders.Loader',
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ]
        },
    },
]

WSGI_APPLICATION = 'jobcore.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases
DATABASES = {
    'default': dj_database_url.config(default=DATABASE_URL)
}

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = os.environ.get('TIME_ZONE', 'UTC')

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'

# STRIPE_PUBLIC_KEY = ""
# STRIPE_SECRET_KEY = ""
# STRIPE_WEBHOOK_SECRET = ""

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# if(os.environ.get('DEBUG') != 'TRUE'):
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
if ENVIRONMENT == 'production':
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(days=9999),  # original: 900
    'JWT_ALLOW_REFRESH': True,
    'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(days=30),
    'JWT_RESPONSE_PAYLOAD_HANDLER': 'api.utils.jwt.jwt_response_payload_handler',
}

REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'api.pagination.HeaderLimitOffsetPagination',
    'PAGE_SIZE': 50,
    'EXCEPTION_HANDLER': 'api.utils.validators.post_exception_handler',
}
# CORS Settings
CORS_ORIGIN_ALLOW_ALL = True
# TODO: Replace localhost with correct Url
# CORS_ORIGIN_WHITELIST = (
#     'localhost'
# )


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{asctime} {levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'debug.log': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/debug.log'),
            'formatter': 'simple',
        },
        'hooks.log': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/hooks.log'),
            'formatter': 'simple',
        },
        'shifts.log': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/shifts.log'),
            'formatter': 'simple',
        },
        'clockin.log': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/clockin.log'),
            'formatter': 'simple',
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'jobcore:general': {
            'handlers': ['console'],
            # 'handlers': ['debug.log', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'jobcore:hooks': {
            # 'handlers': ['console'],
            'handlers': ['hooks.log', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'jobcore:shifts': {
            # 'handlers': ['console'],
            'handlers': ['shifts.log', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'jobcore:clockin': {
            # 'handlers': ['console'],
            'handlers': ['clockin.log', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'jobcore:employee_views:': {
            'handlers': ['console'],
            # 'handlers': ['debug.log', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

EMAIL_NOTIFICATIONS_ENABLED = (os.environ.get('ENABLE_NOTIFICATIONS') == 'TRUE')
