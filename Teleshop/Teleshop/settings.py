"""
Django settings for Teleshop project.

Generated by 'django-admin startproject' using Django 5.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-nkin8cg@4yj$z_u&-kd_=aoev2ze3$wgw+=-5j9)gw6eh5ysm%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'flower_shop',
    'telegrambot',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Teleshop.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Указываем путь к общей папке шаблонов
        'APP_DIRS': True,  # Разрешаем поиск шаблонов в папках приложений
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'flower_shop.context_processors.working_time',
                'flower_shop.context_processors.cart_quantity',
            ],
        },
    },
]

WSGI_APPLICATION = 'Teleshop.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'ru-ru'  # Устанавливаем русский язык
USE_TZ = True
TIME_ZONE = 'Europe/Moscow'  # Устанавливаем московское время
USE_I18N = True  # Включаем поддержку интернационализации
USE_L10N = True  # Включаем локализацию




# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')  # Папка для сбора статических файлов
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'flower_shop/static'),  # Ваша папка со статическими файлами
]


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # Стандартный бэкенд
    'flower_shop.backends.EmailBackend',  # Ваш кастомный бэкенд
]

LOGIN_REDIRECT_URL = 'index'  # Имя URL-шаблона для главной страницы

AUTH_USER_MODEL = 'flower_shop.User'

MEDIA_URL = '/media/'  # URL-префикс для медиафайлов
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # Путь к папке с медиафайлами

LOGIN_URL = 'login'  # Указываем имя URL-шаблона для страницы входа

# Настройки для отправки email (тестирование через консоль)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Если вы хотите использовать реальный email-сервер, настройте следующие параметры:
# EMAIL_HOST = 'smtp.yandex.ru'  # Например, для Yandex
# EMAIL_PORT = 465
# EMAIL_USE_SSL = True
# EMAIL_HOST_USER = 'ваш_email@yandex.ru'
# EMAIL_HOST_PASSWORD = 'ваш_пароль'

TELEGRAM_BOT_TOKEN = '8010538176:AAEnXXncUzx55BhULeRirz_0f43dRw7Hl6o'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

# ALLOWED_HOSTS = [
#     '213.171.31.160',
#     'localhost',  # Разрешить локальный доступ
#     '127.0.0.1',  # Разрешить доступ по IP
# ]

#'1ad0-185-21-13-3.ngrok-free.app',   Разрешить доступ через ngrok

# settings.py
# BASE_URL = 'https://1ad0-185-21-13-3.ngrok-free.app'  # Для локального окружения (ngrok)
# BASE_URL = 'https://ваш-домен.com'  # Для продакшн-окружения
# BASE_URL = 'http://213.171.31.160:8000'

BASE_URL = 'http://176.108.248.61'

YAADMIN_SECRET_CODE = "123"