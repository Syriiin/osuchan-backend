import random
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from minigames.games.base import GameScore


class BaseTask(ABC):
    _registry: dict[str, type[BaseTask]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._registry[cls.type_key] = cls

    type_key: str = ""
    description_template: str = ""

    @classmethod
    @abstractmethod
    def generate_params(cls) -> dict[str, Any]: ...

    @classmethod
    @abstractmethod
    def check(cls, score: GameScore, params: dict[str, Any]) -> bool: ...

    @classmethod
    def get_description(cls, params: dict[str, Any]) -> str:
        return cls.description_template.format(**params)


class AccuracyAboveTask(BaseTask):
    type_key = "accuracy_above"
    description_template = "Get above {min_accuracy}% accuracy"

    @classmethod
    def generate_params(cls):
        return {"min_accuracy": random.randrange(970, 1001) / 10}

    @classmethod
    def check(cls, score, params):
        return score.score_accuracy >= params["min_accuracy"]


class AccuracyBelowTask(BaseTask):
    type_key = "accuracy_below"
    description_template = "Get below {max_accuracy}% accuracy"

    @classmethod
    def generate_params(cls):
        return {"max_accuracy": random.randrange(500, 741) / 10}

    @classmethod
    def check(cls, score, params):
        return score.score_accuracy <= params["max_accuracy"]


class RequiresModTask(BaseTask):
    type_key = "requires_mod"
    description_template = "Play with {mod}"

    @classmethod
    def generate_params(cls):
        return {
            "mod": random.choice(
                ["NF", "EZ", "HD", "HR", "SD", "DT", "HT", "NC", "FL", "SO", "PF"]
            )
        }

    @classmethod
    def check(cls, score, params):
        return params["mod"] in score.score_mods_json


class TvSizeWithDtTask(BaseTask):
    type_key = "tv_size_with_dt"
    description_template = "Play a TV size map with DT"

    @classmethod
    def generate_params(cls):
        return {}

    @classmethod
    def check(cls, score, params):
        return "tv size" in score.beatmap_title.lower() and (
            "DT" in score.score_mods_json or "NC" in score.score_mods_json
        )


class ComboAboveTask(BaseTask):
    type_key = "combo_above"
    description_template = "Score at least {min_combo} combo"

    @classmethod
    def generate_params(cls):
        return {"min_combo": random.randint(1000, 2500)}

    @classmethod
    def check(cls, score, params):
        return score.score_best_combo >= params["min_combo"]


class BpmAboveTask(BaseTask):
    type_key = "bpm_above"
    description_template = "Play a map with BPM over {min_bpm}"

    @classmethod
    def generate_params(cls):
        return {"min_bpm": random.randint(100, 300)}

    @classmethod
    def check(cls, score, params):
        return score.score_bpm > params["min_bpm"]


class BpmBelowTask(BaseTask):
    type_key = "bpm_below"
    description_template = "Play a map with BPM under {max_bpm}"

    @classmethod
    def generate_params(cls):
        return {"max_bpm": random.randint(100, 300)}

    @classmethod
    def check(cls, score, params):
        return score.score_bpm < params["max_bpm"]


class PerfectFcTask(BaseTask):
    type_key = "perfect_fc"
    description_template = "Full combo with a perfect combo"

    @classmethod
    def generate_params(cls):
        return {}

    @classmethod
    def check(cls, score, params):
        return score.score_perfect


class RankEqualsTask(BaseTask):
    type_key = "rank_equals"
    description_template = "Achieve {rank} rank"

    @classmethod
    def generate_params(cls):
        return {"rank": random.choice(["D", "C", "B", "A", "S", "SS", "SH", "SSH"])}

    @classmethod
    def check(cls, score, params):
        return score.score_rank == params["rank"]


class ExactlyOneMissTask(BaseTask):
    type_key = "exactly_one_miss"
    description_template = "Get exactly 1 miss"

    @classmethod
    def generate_params(cls):
        return {}

    @classmethod
    def check(cls, score, params):
        return score.score_count_miss == 1


class MinDifferentModsTask(BaseTask):
    type_key = "min_different_mods"
    description_template = "Use at least {min_mods} different mods"

    @classmethod
    def generate_params(cls):
        return {"min_mods": random.randint(2, 6)}

    @classmethod
    def check(cls, score, params):
        return len(score.score_mods_json) >= params["min_mods"]


class RankedInYearTask(BaseTask):
    type_key = "ranked_in_year"
    description_template = "Play a map ranked in {year}"

    @classmethod
    def generate_params(cls):
        return {"year": random.randint(2007, datetime.now(timezone.utc).year)}

    @classmethod
    def check(cls, score, params):
        return (
            score.beatmap_approval_date is not None
            and score.beatmap_approval_date.year == params["year"]
        )


class MapByCreatorTask(BaseTask):
    type_key = "map_by_creator"
    description_template = "Play a map by {creator_name}"

    creator_names: list[str] = [
        "Hollow Wings",
        "EvilElvis",
        "peppy",
    ]

    @classmethod
    def generate_params(cls):
        return {"creator_name": random.choice(cls.creator_names)}

    @classmethod
    def check(cls, score, params):
        return params["creator_name"].lower() in score.beatmap_creator_name.lower()


class MoreSlidersThanCirclesTask(BaseTask):
    type_key = "more_sliders_than_circles"
    description_template = "Play a map with more sliders than circles"

    @classmethod
    def generate_params(cls):
        return {}

    @classmethod
    def check(cls, score, params):
        hoc = score.beatmap_hitobject_counts
        return hoc.get("sliders", 0) > hoc.get("circles", 0)


class SpinnersAboveTask(BaseTask):
    type_key = "spinners_above"
    description_template = "Play a map with more than {min_spinners} spinners"

    @classmethod
    def generate_params(cls):
        return {"min_spinners": random.randint(3, 5)}

    @classmethod
    def check(cls, score, params):
        return (
            score.beatmap_hitobject_counts.get("spinners", 0) > params["min_spinners"]
        )


class ZeroCirclesTask(BaseTask):
    type_key = "zero_circles"
    description_template = "Play a map with no circles"

    @classmethod
    def generate_params(cls):
        return {}

    @classmethod
    def check(cls, score, params):
        return score.beatmap_hitobject_counts.get("circles", 0) == 0


class OnlyCirclesTask(BaseTask):
    type_key = "only_circles"
    description_template = "Play a map with only circles"

    @classmethod
    def generate_params(cls):
        return {}

    @classmethod
    def check(cls, score, params):
        hoc = score.beatmap_hitobject_counts
        return (
            hoc.get("circles", 0) > 0
            and hoc.get("sliders", 0) == 0
            and hoc.get("spinners", 0) == 0
        )


class OdHigherThanArTask(BaseTask):
    type_key = "od_higher_than_ar"
    description_template = "Play a map where OD is higher than AR"

    @classmethod
    def generate_params(cls):
        return {}

    @classmethod
    def check(cls, score, params):
        return score.score_overall_difficulty > score.score_approach_rate


class LongerDiffThanArtistTitleTask(BaseTask):
    type_key = "longer_diff_than_artist_title"
    description_template = (
        "Play a map with a difficulty name longer than the artist and title combined"
    )

    @classmethod
    def generate_params(cls):
        return {}

    @classmethod
    def check(cls, score, params):
        return len(score.beatmap_difficulty_name) > len(score.beatmap_artist) + len(
            score.beatmap_title
        )


class ResultsScreen727Task(BaseTask):
    type_key = "results_screen_727"
    description_template = "Have a 727 in the results screen stats"

    @classmethod
    def generate_params(cls):
        return {}

    @classmethod
    def check(cls, score, params):
        fields = [
            str(score.score_score),
            str(score.score_best_combo),
            str(score.score_count_300),
            str(score.score_count_100),
            str(score.score_count_50),
            str(score.score_count_miss),
        ]
        return any("727" in field for field in fields)


class FcWithMaxAccTask(BaseTask):
    type_key = "fc_with_max_acc"
    description_template = "FC with at most {max_accuracy}% accuracy"

    @classmethod
    def generate_params(cls):
        return {"max_accuracy": random.randint(40, 70)}

    @classmethod
    def check(cls, score, params):
        return score.score_perfect and score.score_accuracy <= params["max_accuracy"]


class LongPlayLowComboTask(BaseTask):
    type_key = "long_play_low_combo"
    description_template = (
        "More than {min_minutes} min with at most {max_combo} combo, no 100s or 50s"
    )

    @classmethod
    def generate_params(cls):
        return {
            "min_minutes": random.randint(2, 5),
            "max_combo": random.randint(30, 100),
        }

    @classmethod
    def check(cls, score, params):
        return (
            score.score_length / 60 > params["min_minutes"]
            and score.score_best_combo <= params["max_combo"]
            and score.score_count_100 == 0
            and score.score_count_50 == 0
        )


class More50sThan300sTask(BaseTask):
    type_key = "more_50s_than_300s"
    description_template = "Get more 50s than 300s"

    @classmethod
    def generate_params(cls):
        return {}

    @classmethod
    def check(cls, score, params):
        return score.score_count_50 > score.score_count_300


class Zero300sNoNfTask(BaseTask):
    type_key = "zero_300s_no_nf"
    description_template = "Zero 300s (no NF)"

    @classmethod
    def generate_params(cls):
        return {}

    @classmethod
    def check(cls, score, params):
        return score.score_count_300 == 0 and "NF" not in score.score_mods_json


class HighAccHighOdTask(BaseTask):
    type_key = "high_acc_high_od"
    description_template = "Over {min_accuracy}% acc on at least OD 10"

    @classmethod
    def generate_params(cls):
        return {"min_accuracy": random.randrange(975, 1001) / 10}

    @classmethod
    def check(cls, score, params):
        return (
            score.score_accuracy > params["min_accuracy"]
            and score.score_overall_difficulty >= 10
        )


class FcAboveAr10Task(BaseTask):
    type_key = "fc_above_ar_10"
    description_template = "FC above AR 10"

    @classmethod
    def generate_params(cls):
        return {}

    @classmethod
    def check(cls, score, params):
        return score.score_perfect and score.score_approach_rate > 10


class ClearFamousMapTask(BaseTask):
    type_key = "clear_famous_map"
    description_template = "Clear {map_id}"

    famous_map_ids: dict[int, str] = {
        942356: "Notch Hell",
        131891: "The Big Black",
    }

    @classmethod
    def generate_params(cls):
        return {"map_id": random.choice(list(cls.famous_map_ids))}

    @classmethod
    def get_description(cls, params):
        return f"Clear {cls.famous_map_ids[params['map_id']]}"

    @classmethod
    def check(cls, score, params):
        return score.beatmap_id == params["map_id"]


class HdflTask(BaseTask):
    type_key = "hdfl"
    description_template = "Play with HD and FL"

    @classmethod
    def generate_params(cls):
        return {}

    @classmethod
    def check(cls, score, params):
        return "HD" in score.score_mods_json and "FL" in score.score_mods_json


class StarsAboveTask(BaseTask):
    type_key = "stars_above"
    description_template = "Play a {min_stars} star map"

    @classmethod
    def generate_params(cls):
        return {"min_stars": random.randint(5, 10)}

    @classmethod
    def check(cls, score, params):
        return (
            score.score_difficulty_total is not None
            and score.score_difficulty_total >= params["min_stars"]
        )


class PpAboveTask(BaseTask):
    type_key = "pp_above"
    description_template = "Earn at least {min_pp}pp"

    @classmethod
    def generate_params(cls):
        return {"min_pp": random.randint(200, 1000)}

    @classmethod
    def check(cls, score, params):
        return (
            score.score_performance_total is not None
            and score.score_performance_total >= params["min_pp"]
        )


task_registry: dict[str, type[BaseTask]] = BaseTask._registry
