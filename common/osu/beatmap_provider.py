import os
import urllib.request
from abc import ABC, abstractmethod
from typing import Type, Union

from django.conf import settings
from django.utils.module_loading import import_string


class BeatmapNotFoundException(Exception):
    pass


class AbstractBeatmapProvider(ABC):
    @abstractmethod
    def get_beatmap_file(self, beatmap_id: str) -> str:
        raise NotImplementedError()


class LiveBeatmapProvider(AbstractBeatmapProvider):
    def get_beatmap_file(self, beatmap_id: str) -> str:
        beatmap_path = os.path.join(settings.BEATMAP_CACHE_PATH, str(beatmap_id))

        if not os.path.isfile(beatmap_path):
            beatmap_url = f"{settings.BEATMAP_DL_URL}{beatmap_id}"
            urllib.request.urlretrieve(beatmap_url, beatmap_path)
            if os.path.getsize(beatmap_path) == 0:
                os.remove(beatmap_path)
                raise BeatmapNotFoundException(
                    f"Beatmap {beatmap_id} not found at {beatmap_url}"
                )

        return beatmap_path


class StubBeatmapProvider(AbstractBeatmapProvider):
    def get_beatmap_file(self, beatmap_id: str) -> Union[str, None]:
        beatmap_path = os.path.join(
            os.path.dirname(__file__), "stubdata", "beatmap_provider", str(beatmap_id)
        )

        if not os.path.exists(beatmap_path):
            raise BeatmapNotFoundException(
                f"Beatmap {beatmap_id} not found at {beatmap_path}"
            )

        return beatmap_path


BeatmapProvider: Type[AbstractBeatmapProvider] = import_string(
    settings.BEATMAP_PROVIDER_CLASS
)
