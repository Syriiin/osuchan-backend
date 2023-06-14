from abc import ABC, abstractmethod
from typing import Type

import httpx
from django.conf import settings
from django.utils.module_loading import import_string


class InvalidWebhookUrlError(ValueError):
    pass


class AbstractDiscordWebhookSender(ABC):
    @abstractmethod
    def send(self, webhook_url: str, data: dict):
        raise NotImplementedError()


class LiveDiscordWebhookSender(AbstractDiscordWebhookSender):
    def send(self, webhook_url: str, data: dict) -> None:
        if not webhook_url.startswith("https://discord.com/api/webhooks/"):
            raise InvalidWebhookUrlError(webhook_url)

        httpx.post(
            webhook_url,
            json=data,
        )


class DummyDiscordWebhookSender(AbstractDiscordWebhookSender):
    def send(self, webhook_url: str, data: dict):
        pass


DiscordWebhookSender: Type[AbstractDiscordWebhookSender] = import_string(
    settings.DISCORD_WEBHOOK_SENDER_CLASS
)
