"""
Django settings for osuchan
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "debug_toolbar",  # django debug toolbar
    "osuauth.apps.OsuauthConfig",  # osu auth and accounts
    "users.apps.UsersConfig",  # api for users
    "profiles.apps.ProfilesConfig",  # api for profiles
    "leaderboards.apps.LeaderboardsConfig",  # api for leaderboards
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "middleware.logging.DiscordErrorLoggingMiddleware",
]

ROOT_URLCONF = "osuchan.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "osuchan.wsgi.application"


# Auth
# https://docs.djangoproject.com/en/dev/ref/settings/#auth

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "osuauth.backends.OsuBackend",
]

AUTH_USER_MODEL = "osuauth.User"


# Password validation
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_URL = "/backendstatic/"

STATIC_ROOT = os.path.join(BASE_DIR, "static/")

STATICFILES_DIRS = []


# osu! API

# v2
OSU_OAUTH_AUTHORISE_URL = "https://osu.ppy.sh/oauth/authorize"
OSU_OAUTH_TOKEN_URL = "https://osu.ppy.sh/oauth/token"
OSU_OAUTH_SCOPE = "identify friends.read"
OSU_API_V2_BASE_URL = "https://osu.ppy.sh/api/v2/"

# v1
OSU_API_V1_BASE_URL = "https://osu.ppy.sh/api/"

# Beatmaps
BEATMAP_DL_URL = "https://osu.ppy.sh/osu/"


# DifficultyCalculation
DIFFICULTY_CALCULATOR_CLASS = (
    "common.osu.difficultycalculator.RosuppDifficultyCalculator"
)

# Environment specific overrides and sensitive settings

from local_settings import *
