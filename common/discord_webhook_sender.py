from abc import ABC, abstractmethod
from typing import Type

import httpx
from django.conf import settings
from django.utils.module_loading import import_string


class AbstractDiscordWebhookSender(ABC):
    @abstractmethod
    def send(self, webhook_url: str, data: dict):
        pass


class LiveDiscordWebhookSender(AbstractDiscordWebhookSender):
    def send(self, webhook_url: str, data: dict) -> None:
        # TODO: do webhook url validation
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
