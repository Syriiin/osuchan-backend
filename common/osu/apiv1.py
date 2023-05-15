from abc import ABC, abstractmethod

import requests
from django.conf import settings

API_KEY = settings.OSU_API_V1_KEY
BASE_URL = settings.OSU_API_V1_BASE_URL


class AbstractOsuApiV1(ABC):
    @abstractmethod
    def get_beatmaps(self, beatmap_id=None):
        pass

    @abstractmethod
    def get_user(self, user_id, user_id_type="id", gamemode=None):
        pass

    @abstractmethod
    def get_scores(self, beatmap_id, user_id=None, user_id_type="id", gamemode=None):
        pass

    @abstractmethod
    def get_user_best(self, user_id, user_id_type="id", gamemode=None, limit=None):
        pass

    @abstractmethod
    def get_user_recent(self, user_id, user_id_type="id", gamemode=None, limit=None):
        pass


class OsuApiV1(AbstractOsuApiV1):
    def __get_legacy_endpoint(self, endpoint_name, **kwargs):
        # Remove any None arguments passed in kwargs
        payload = {k: v for k, v in kwargs.items() if v is not None}

        # Add api key to payload
        payload["k"] = API_KEY

        # Return result of GET request
        return requests.get(BASE_URL + endpoint_name, params=payload).json()

    def get_beatmaps(self, beatmap_id=None):
        return self.__get_legacy_endpoint("get_beatmaps", b=beatmap_id)

    def get_user(self, user_id, user_id_type="id", gamemode=None):
        try:
            return self.__get_legacy_endpoint(
                "get_user", u=user_id, type=user_id_type, m=gamemode
            )[0]
        except IndexError:
            return None

    def get_scores(self, beatmap_id, user_id=None, user_id_type="id", gamemode=None):
        return self.__get_legacy_endpoint(
            "get_scores", b=beatmap_id, u=user_id, type=user_id_type, m=gamemode
        )

    def get_user_best(self, user_id, user_id_type="id", gamemode=None, limit=None):
        return self.__get_legacy_endpoint(
            "get_user_best", u=user_id, type=user_id_type, m=gamemode, limit=limit
        )

    def get_user_recent(self, user_id, user_id_type="id", gamemode=None, limit=None):
        return self.__get_legacy_endpoint(
            "get_user_recent", u=user_id, type=user_id_type, m=gamemode, limit=limit
        )
