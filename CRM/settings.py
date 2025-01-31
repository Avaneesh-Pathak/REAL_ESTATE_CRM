from pathlib import Path
import os

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: don't run with DEBUG=True in production!
# DEBUG = os.getenv("DEBUG", "False") == "True"  # Default to False in production
DEBUG = False
SECRET_KEY = os.getenv(
    "SECRET_KEY", 
    "django-insecure-_-s#%_=bpv+xk2c4y_tuiea0uw_e7gw!63afunys%vx5-fxyt0"
)  # Load from environment in production

# Allowed hosts
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "127.0.0.1").split(",")  # Set environment variable for production

# TWILIO credentials (use environment variables in production)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "AC1aecf01fb386ff58a11d18179e2e0b7b")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "794dfc0b9d3c23a62d5382d25a282aff")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "+12565888618")

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
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Static files middleware
    'django.contrib.sessions.middleware.SessionMiddleware',  # Required for session management
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # CSRF protection
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # Required for admin and auth
    'django.contrib.messages.middleware.MessageMiddleware',  # Required for messages framework
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
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files and media
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "static_root"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

# Custom user model
AUTH_USER_MODEL = 'leads.User'

# Authentication
LOGIN_REDIRECT_URL = "/dashboard"
LOGIN_URL = "/dashboard"
LOGOUT_REDIRECT_URL = "/"

# Crispy forms
CRISPY_TEMPLATE_PACK = "tailwind"

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'avaneeshpathak900@gmail.com'
EMAIL_HOST_PASSWORD = 'yvga yoxu bzse epbd'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

BASE_DIR = Path(__file__).resolve().parent.parent

# Ensure the logs directory exists
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGS_DIR, 'app_errors.log').replace('\\', '/'),
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