"""
Local settings for ...
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Security

# SECURITY WARNING: keep the secret key used in production secret!
# NOTE: use django.core.management.utils.get_random_secret_key() to generate a suitable key
SECRET_KEY = ""

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# NOTE: must not be empty when DEBUG is False
ALLOWED_HOSTS = []


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': ''
    }
}
