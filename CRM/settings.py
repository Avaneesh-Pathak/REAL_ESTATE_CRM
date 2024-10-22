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
ALLOWED_HOSTS =[]

# Installed apps
INSTALLED_APPS = [
    'whitenoise.runserver_nostatic',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third Party Apps
    'crispy_forms',
    'crispy_tailwind',
    'tailwind',
    'theme',
    'widget_tweaks',
    
    # Local Apps
    'leads',
    'agents',
]

# Middleware
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
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
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "static_root"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

AUTH_USER_MODEL = 'leads.User'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Authentication
LOGIN_REDIRECT_URL = "/dashboard"
LOGIN_URL = "/dashboard"
LOGOUT_REDIRECT_URL = "/"

CRISPY_TEMPLATE_PACK = "tailwind"

# Email settings
# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
# EMAIL_HOST_USER = env("EMAIL_HOST_USER")
# EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
# EMAIL_USE_TLS = True
# EMAIL_PORT = env.int("EMAIL_PORT")
# DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")

# # Secure settings for production
# if not DEBUG:
#     SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
#     SECURE_SSL_REDIRECT = True
#     SESSION_COOKIE_SECURE = True
#     CSRF_COOKIE_SECURE = True
#     SECURE_BROWSER_XSS_FILTER = True
#     SECURE_CONTENT_TYPE_NOSNIFF = True
#     SECURE_HSTS_SECONDS = 31536000
#     SECURE_HSTS_INCLUDE_SUBDOMAINS = True
#     SECURE_HSTS_PRELOAD = True
#     X_FRAME_OPTIONS = "DENY"


# AWS_ACCESS_KEY_ID ='AKIAYM7PN3PCBA4F2K6R'
# AWS_SECRET_ACCESS_KEY ='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'
# AWS_STORAGE_BUCKET_NAME='djcrm'
# AWS_S3_SIGNATURE_NAME='s3v4'
# AWS_S3_REGION_NAME='eu-north-1'
# AWS_S3_FILE_OVERWRITE= False
# AWS_DEFAULT_ACL=None
# AWS_S3_VERIFY=True
# DEFAULT_FILE_STORAGE='storages.backends.s3boto3.S3Boto3Storage'


# Static and media settings (optional)

# MEDIA_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/'



