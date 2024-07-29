"""
Django settings for osuchan
"""

import os
from datetime import timedelta

from celery.schedules import crontab
from pydantic_settings import BaseSettings

from common.osu.enums import Gamemode


class EnvSettings(BaseSettings):
    SECRET_KEY: str
    DEBUG: bool
    ALLOWED_HOSTS: list[str]
    FRONTEND_URL: str
    POSTGRES_DB_NAME: str
    POSTGRES_DB_USER: str
    POSTGRES_DB_PASSWORD: str
    POSTGRES_DB_HOST: str
    POSTGRES_DB_PORT: str
    REDIS_HOST: str
    REDIS_PORT: str
    CELERY_USER: str
    CELERY_PASSWORD: str
    CELERY_HOST: str
    CELERY_PORT: str
    DIFFICALCY_OSU_HOST: str
    DIFFICALCY_TAIKO_HOST: str
    DIFFICALCY_CATCH_HOST: str
    DIFFICALCY_MANIA_HOST: str
    OSU_CLIENT_ID: str
    OSU_CLIENT_SECRET: str
    OSU_CLIENT_REDIRECT_URI: str
    OSU_API_V1_KEY: str
    DISCORD_WEBHOOK_URL_ERROR_LOG: str
    USE_DUMMY_ERROR_REPORTER: bool
    USE_DUMMY_DISCORD_WEBHOOK_SENDER: bool
    USE_STUB_OSU_API_V1: bool
    USE_STUB_BEATMAP_PROVIDER: bool
    USE_STUB_OSU_OAUTH: bool


env_settings = EnvSettings()


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Security

# SECURITY WARNING: keep the secret key used in production secret!
# NOTE: use django.core.management.utils.get_random_secret_key() to generate a suitable key
#   eg. docker run -it python sh -c 'pip install django && python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"'
SECRET_KEY = env_settings.SECRET_KEY

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_settings.DEBUG

# NOTE: must not be empty when DEBUG is False
ALLOWED_HOSTS = [
    "api",  # hostname inside the docker network
] + env_settings.ALLOWED_HOSTS

CSRF_TRUSTED_ORIGINS = [env_settings.FRONTEND_URL]

# IPs allowed to use debug toolbar (docker makes this a little more complicated)
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#configure-internal-ips
if DEBUG:
    import socket  # only if you haven't already imported this

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + [
        "127.0.0.1",
        "10.0.2.2",
    ]


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
    "django_prometheus",
    "osuauth.apps.OsuauthConfig",  # osu auth and accounts
    "users.apps.UsersConfig",  # api for users
    "profiles.apps.ProfilesConfig",  # api for profiles
    "leaderboards.apps.LeaderboardsConfig",  # api for leaderboards
]

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "middleware.logging.DiscordErrorLoggingMiddleware",
    "osuauth.middleware.LastActiveMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
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
]

USE_STUB_OSU_OAUTH = env_settings.USE_STUB_OSU_OAUTH

if USE_STUB_OSU_OAUTH:
    AUTHENTICATION_BACKENDS.append("osuauth.backends.StubOsuBackend")
else:
    AUTHENTICATION_BACKENDS.append("osuauth.backends.OsuBackend")

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


# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django_prometheus.db.backends.postgresql",
        "NAME": env_settings.POSTGRES_DB_NAME,
        "USER": env_settings.POSTGRES_DB_USER,
        "PASSWORD": env_settings.POSTGRES_DB_PASSWORD,
        "HOST": env_settings.POSTGRES_DB_HOST,
        "PORT": env_settings.POSTGRES_DB_PORT,
    }
}


# Cache
# https://docs.djangoproject.com/en/dev/ref/settings/#caches

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{env_settings.REDIS_HOST}:{env_settings.REDIS_PORT}/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}


# Celery
# https://docs.celeryproject.org/en/latest/userguide/configuration.html

CELERY_BROKER_URL = f"amqp://{env_settings.CELERY_USER}:{env_settings.CELERY_PASSWORD}@{env_settings.CELERY_HOST}:{env_settings.CELERY_PORT}"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_WORKER_MAX_MEMORY_PER_CHILD = 250000  # 250MB TODO: investigate this memory leak

CELERY_BEAT_SCHEDULE = {
    "update-top-global-members-every-day": {
        "task": "profiles.tasks.dispatch_update_all_global_leaderboard_top_members",
        "schedule": crontab(minute="0", hour="0"),  # midnight UTC
        "kwargs": {
            "limit": 100,
            "cooldown_seconds": timedelta(hours=12).total_seconds(),
        },
    },
    "update-loved-beatmaps-every-month": {
        "task": "profiles.tasks.update_loved_beatmaps",
        "schedule": crontab(minute="0", hour="0", day_of_month="1"),
    },
    "update-coe-top-members-osu-every-10-minutes": {
        "task": "profiles.tasks.dispatch_update_community_leaderboard_members",
        "schedule": 60 * 10,
        "args": (804, 50),
    },
    "update-coe-top-members-taiko-every-10-minutes": {
        "task": "profiles.tasks.dispatch_update_community_leaderboard_members",
        "schedule": 60 * 10,
        "args": (805, 50),
    },
    "update-coe-top-members-catch-every-10-minutes": {
        "task": "profiles.tasks.dispatch_update_community_leaderboard_members",
        "schedule": 60 * 10,
        "args": (806, 50),
    },
    "update-coe-top-members-mania-every-10-minutes": {
        "task": "profiles.tasks.dispatch_update_community_leaderboard_members",
        "schedule": 60 * 10,
        "args": (807, 50),
    },
    "update-coe-all-members-osu-every-hour": {
        "task": "profiles.tasks.dispatch_update_community_leaderboard_members",
        "schedule": 60 * 60,
        "args": (804, 1000),
    },
    "update-coe-all-members-taiko-every-hour": {
        "task": "profiles.tasks.dispatch_update_community_leaderboard_members",
        "schedule": 60 * 60,
        "args": (805, 1000),
    },
    "update-coe-all-members-catch-every-hour": {
        "task": "profiles.tasks.dispatch_update_community_leaderboard_members",
        "schedule": 60 * 60,
        "args": (806, 1000),
    },
    "update-coe-all-members-mania-every-hour": {
        "task": "profiles.tasks.dispatch_update_community_leaderboard_members",
        "schedule": 60 * 60,
        "args": (807, 1000),
    },
    "send-coe-podium-osu-every-day": {
        "task": "leaderboards.tasks.send_leaderboard_podium_notification",
        "schedule": crontab(minute="0", hour="20"),  # 22:00 netherlands time
        "args": (804,),
    },
    "send-coe-podium-taiko-every-day": {
        "task": "leaderboards.tasks.send_leaderboard_podium_notification",
        "schedule": crontab(minute="0", hour="20"),  # 22:00 netherlands time
        "args": (805,),
    },
    "send-coe-podium-catch-every-day": {
        "task": "leaderboards.tasks.send_leaderboard_podium_notification",
        "schedule": crontab(minute="0", hour="20"),  # 22:00 netherlands time
        "args": (806,),
    },
    "send-coe-podium-mania-every-day": {
        "task": "leaderboards.tasks.send_leaderboard_podium_notification",
        "schedule": crontab(minute="0", hour="20"),  # 22:00 netherlands time
        "args": (807,),
    },
}


# Logging

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"level": "INFO", "class": "logging.StreamHandler"}},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": True}
    },
}


# Django REST framework
# https://www.django-rest-framework.org/api-guide/settings/

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/minute",
        "user": "45/minute",
        "anon": "1000/day",
        "user": "1500/day",
    },
}

if DEBUG:
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"].append(
        "rest_framework.renderers.BrowsableAPIRenderer"
    )


# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_URL = "/backendstatic/"

STATIC_ROOT = os.path.join(BASE_DIR, "static/")

STATICFILES_DIRS = []


# Frontend config

FRONTEND_URL = env_settings.FRONTEND_URL


# osu! API v2

OSU_OAUTH_AUTHORISE_URL = "https://osu.ppy.sh/oauth/authorize"
OSU_OAUTH_TOKEN_URL = "https://osu.ppy.sh/oauth/token"
OSU_OAUTH_SCOPE = "identify friends.read"
OSU_API_V2_BASE_URL = "https://osu.ppy.sh/api/v2/"

OSU_CLIENT_ID = env_settings.OSU_CLIENT_ID
OSU_CLIENT_SECRET = env_settings.OSU_CLIENT_SECRET
OSU_CLIENT_REDIRECT_URI = env_settings.OSU_CLIENT_REDIRECT_URI


# osu! API v1

OSU_API_V1_BASE_URL = "https://osu.ppy.sh/api/"

OSU_API_V1_KEY = env_settings.OSU_API_V1_KEY


if env_settings.USE_STUB_OSU_API_V1:
    OSU_API_V1_CLASS = "common.osu.apiv1.StubOsuApiV1"
else:
    OSU_API_V1_CLASS = "common.osu.apiv1.LiveOsuApiV1"


# Beatmaps

BEATMAP_DL_URL = "https://osu.ppy.sh/osu/"
BEATMAP_CACHE_PATH = "/beatmaps"

if env_settings.USE_STUB_BEATMAP_PROVIDER:
    BEATMAP_PROVIDER_CLASS = "common.osu.beatmap_provider.StubBeatmapProvider"
else:
    BEATMAP_PROVIDER_CLASS = "common.osu.beatmap_provider.LiveBeatmapProvider"


# Difficulty calculation

DIFFICULTY_CALCULATOR_CLASSES = {
    "oppai": "common.osu.difficultycalculator.OppaiDifficultyCalculator",
    "rosupp": "common.osu.difficultycalculator.RosuppDifficultyCalculator",
    "difficalcy-osu": "common.osu.difficultycalculator.DifficalcyOsuDifficultyCalculator",
    "difficalcy-taiko": "common.osu.difficultycalculator.DifficalcyTaikoDifficultyCalculator",
    "difficalcy-catch": "common.osu.difficultycalculator.DifficalcyCatchDifficultyCalculator",
    "difficalcy-mania": "common.osu.difficultycalculator.DifficalcyManiaDifficultyCalculator",
}

DEFAULT_DIFFICULTY_CALCULATORS = {
    Gamemode.STANDARD: "rosupp",
    Gamemode.TAIKO: "difficalcy-taiko",
    Gamemode.CATCH: "difficalcy-catch",
    Gamemode.MANIA: "difficalcy-mania",
}

DIFFICALCY_OSU_URL = f"http://{env_settings.DIFFICALCY_OSU_HOST}"
DIFFICALCY_TAIKO_URL = f"http://{env_settings.DIFFICALCY_TAIKO_HOST}"
DIFFICALCY_CATCH_URL = f"http://{env_settings.DIFFICALCY_CATCH_HOST}"
DIFFICALCY_MANIA_URL = f"http://{env_settings.DIFFICALCY_MANIA_HOST}"


# Error reporting

if env_settings.USE_DUMMY_ERROR_REPORTER:
    ERROR_REPORTER_CLASS = "common.error_reporter.DummyErrorReporter"
else:
    ERROR_REPORTER_CLASS = "common.error_reporter.DiscordErrorReporter"

DISCORD_WEBHOOK_URL_ERROR_LOG = env_settings.DISCORD_WEBHOOK_URL_ERROR_LOG


# Discord webhooks

if env_settings.USE_DUMMY_DISCORD_WEBHOOK_SENDER:
    DISCORD_WEBHOOK_SENDER_CLASS = (
        "common.discord_webhook_sender.DummyDiscordWebhookSender"
    )
else:
    DISCORD_WEBHOOK_SENDER_CLASS = (
        "common.discord_webhook_sender.LiveDiscordWebhookSender"
    )
