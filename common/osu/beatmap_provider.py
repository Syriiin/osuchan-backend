import os
import urllib.request
from abc import ABC, abstractmethod
from typing import Type, Union

from django.conf import settings
from django.utils.module_loading import import_string


class AbstractBeatmapProvider(ABC):
    @abstractmethod
    def get_beatmap_file(self, beatmap_id: int) -> str:
        raise NotImplementedError()


class LiveBeatmapProvider(AbstractBeatmapProvider):
    def get_beatmap_file(self, beatmap_id: int) -> str:
        beatmap_path = os.path.join(settings.BEATMAP_CACHE_PATH, str(beatmap_id))

        if not os.path.isfile(beatmap_path):
            beatmap_url = f"{settings.BEATMAP_DL_URL}{beatmap_id}"
            urllib.request.urlretrieve(beatmap_url, beatmap_path)

        return beatmap_path


class StubBeatmapProvider(AbstractBeatmapProvider):
    def get_beatmap_file(self, beatmap_id: int) -> Union[str, None]:
        beatmap_path = os.path.join(
            os.path.dirname(__file__), "stubdata", "beatmap_provider", str(beatmap_id)
        )

        if not os.path.exists(beatmap_path):
            return None

        return beatmap_path


BeatmapProvider: Type[AbstractBeatmapProvider] = import_string(
    settings.BEATMAP_PROVIDER_CLASS
)
