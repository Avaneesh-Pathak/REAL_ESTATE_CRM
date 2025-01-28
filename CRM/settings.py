from pathlib import Path
import os
# import environ

# # Initialize environment variables
# env = environ.Env(
#     DEBUG=(bool, False),  # Default DEBUG to False
#     EMAIL_PORT=(int, 587),  # Default email port to 587
# )

# # Read .env file
# environ.Env.read_env()

# # Retrieve environment variables
# DEBUG = env('DEBUG')
# SECRET_KEY = env('SECRET_KEY')
SECRET_KEY = "django-insecure-_-s#%_=bpv+xk2c4y_tuiea0uw_e7gw!63afunys%vx5-fxyt0"

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# settings.py
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

DEBUG = True

# Allowed hosts (adjust for production)
ALLOWED_HOSTS =['0.0.0.0','127.0.0.1']


TWILIO_ACCOUNT_SID = 'AC1aecf01fb386ff58a11d18179e2e0b7b'
TWILIO_AUTH_TOKEN = '794dfc0b9d3c23a62d5382d25a282aff'
TWILIO_PHONE_NUMBER = '+12565888618'


# Installed apps
INSTALLED_APPS = [
    'whitenoise.runserver_nostatic',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    # Third Party Apps
    'crispy_forms',
    'crispy_tailwind',
    'tailwind',
    'theme',
    'widget_tweaks',
    'django_distill',
   
    
    # Local Apps
    'leads',
   
    'agents',
]

# Middleware
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'CRM.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'CRM.wsgi.application'

# Database configuration

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Password validation
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'  # or your local timezone
USE_TZ = True
USE_I18N = True
USE_L10N = True




# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "static_root"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

AUTH_USER_MODEL = 'leads.User'

BASE_DIR = Path(__file__).resolve().parent.parent

# settings.py

import os

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'app_errors.log').replace('\\','/'),  # Ensure path is correct
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'app_errors': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

# Authentication
LOGIN_REDIRECT_URL = "/dashboard"
LOGIN_URL = "/dashboard"
LOGOUT_REDIRECT_URL = "/"

CRISPY_TEMPLATE_PACK = "tailwind"

# Email settings
# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend"
# Use an actual email backend for production, such as:
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'avaneeshpathak900@gmail.com'
EMAIL_HOST_PASSWORD = 'yvga yoxu bzse epbd'


