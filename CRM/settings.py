
from pathlib import Path
import environ

env = environ.Env(
    DEBUG=(bool, False))  # Initializes DEBUG with a default False value


READ_DOT_ENV_FILE = env.bool('READ_DOT_ENV_FILE', default=False)
if READ_DOT_ENV_FILE:
    environ.Env.read_env()  # Reads .env file if READ_DOT_ENV_FILE is set to True
 

# False if not in os.environ
DEBUG = env('DEBUG')  # Retrieves DEBUG value from .env or raises an error if missing
SECRET_KEY = env('SECRET_KEY')  # Retrieves SECRET_KEY from .env or raises an error if missing
print(DEBUG, SECRET_KEY)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'whitenoise.runserver_nostatic',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    #Third Part Apps
    'crispy_forms',
    'crispy_tailwind',
    
    # Local Apps
    'leads',
    'agents',
]

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


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',  # PostgreSQL as the database engine
        'NAME': env("DB_NAME"),  # Retrieves database name from .env
        'USER': env("DB_USER"),  # Retrieves database user from .env
        'PASSWORD': env("DB_PASSWORD"),  # Retrieves database password from .env
        'HOST': env("DB_HOST"),  # Retrieves database host from .env
        'PORT': env("DB_PORT"),  # Retrieves database port from .env
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static"
]

STATIC_ROOT = "static_root"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedMainifestStaticFilesStorage'
AUTH_USER_MODEL = 'leads.User'  # 'leads' is the app name, 'User' is the model name
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"  
LOGIN_REDIRECT_URL="/leads"
LOGIN_URL="/login"
LOGOUT_REDIRECT_URL = "/"

CRISPY_TEMPLATE_PACK = "tailwind"
CRISPY_ALLOWED_TEMPLATE_PACK = "tailwind"






