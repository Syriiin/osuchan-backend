from datetime import datetime

from minigames.games.tasks import task_registry
from minigames.games.test_helpers import _game_score


class TestAllTasks:
    def test_accuracy_above(self):
        score = _game_score(score_accuracy=98)
        assert task_registry["accuracy_above"].check(score, {"min_accuracy": 97})

    def test_accuracy_below(self):
        score = _game_score(score_accuracy=60)
        assert task_registry["accuracy_below"].check(score, {"max_accuracy": 70})

    def test_requires_mod(self):
        score = _game_score(score_mods_json={"HD": {}})
        assert task_registry["requires_mod"].check(score, {"mod": "HD"})

    def test_tv_size_with_dt(self):
        score = _game_score(score_mods_json={"DT": {}}, beatmap_title="TV Size")
        assert task_registry["tv_size_with_dt"].check(score, {})

    def test_combo_above(self):
        score = _game_score(score_best_combo=2000)
        assert task_registry["combo_above"].check(score, {"min_combo": 1500})

    def test_bpm_above(self):
        score = _game_score(score_bpm=250)
        assert task_registry["bpm_above"].check(score, {"min_bpm": 200})

    def test_bpm_below(self):
        score = _game_score(score_bpm=150)
        assert task_registry["bpm_below"].check(score, {"max_bpm": 200})

    def test_perfect_fc(self):
        score = _game_score(score_perfect=True)
        assert task_registry["perfect_fc"].check(score, {})

    def test_rank_equals(self):
        score = _game_score(score_rank="S")
        assert task_registry["rank_equals"].check(score, {"rank": "S"})

    def test_exactly_one_miss(self):
        score = _game_score(score_count_miss=1)
        assert task_registry["exactly_one_miss"].check(score, {})

    def test_min_different_mods(self):
        score = _game_score(score_mods_json={"DT": {}, "HR": {}, "HD": {}})
        assert task_registry["min_different_mods"].check(score, {"min_mods": 2})

    def test_ranked_in_year(self):
        score = _game_score(beatmap_approval_date=datetime(2015, 1, 1))
        assert task_registry["ranked_in_year"].check(score, {"year": 2015})

    def test_map_by_creator(self):
        score = _game_score(beatmap_creator_name="Hollow Wings")
        assert task_registry["map_by_creator"].check(
            score, {"creator_name": "Hollow Wings"}
        )

    def test_more_sliders_than_circles(self):
        score = _game_score(beatmap_hitobject_counts={"sliders": 10, "circles": 5})
        assert task_registry["more_sliders_than_circles"].check(score, {})

    def test_spinners_above(self):
        score = _game_score(beatmap_hitobject_counts={"spinners": 5})
        assert task_registry["spinners_above"].check(score, {"min_spinners": 3})

    def test_zero_circles(self):
        score = _game_score(beatmap_hitobject_counts={"circles": 0})
        assert task_registry["zero_circles"].check(score, {})

    def test_only_circles(self):
        score = _game_score(
            beatmap_hitobject_counts={"circles": 10, "sliders": 0, "spinners": 0}
        )
        assert task_registry["only_circles"].check(score, {})

    def test_od_higher_than_ar(self):
        score = _game_score(score_overall_difficulty=10, score_approach_rate=8)
        assert task_registry["od_higher_than_ar"].check(score, {})

    def test_longer_diff_than_artist_title(self):
        score = _game_score(
            beatmap_difficulty_name="Very Long Difficulty Name",
            beatmap_artist="a",
            beatmap_title="b",
        )
        assert task_registry["longer_diff_than_artist_title"].check(score, {})

    def test_results_screen_727(self):
        score = _game_score(score_score=727)
        assert task_registry["results_screen_727"].check(score, {})

    def test_fc_with_max_acc(self):
        score = _game_score(score_perfect=True, score_accuracy=50)
        assert task_registry["fc_with_max_acc"].check(score, {"max_accuracy": 60})

    def test_long_play_low_combo(self):
        score = _game_score(
            score_length=3601, score_best_combo=50, score_count_100=0, score_count_50=0
        )
        assert task_registry["long_play_low_combo"].check(
            score, {"min_minutes": 60, "max_combo": 100}
        )

    def test_more_50s_than_300s(self):
        score = _game_score(score_count_50=10, score_count_300=5)
        assert task_registry["more_50s_than_300s"].check(score, {})

    def test_zero_300s_no_nf(self):
        score = _game_score(score_count_300=0, score_mods_json={"HD": {}})
        assert task_registry["zero_300s_no_nf"].check(score, {})

    def test_high_acc_high_od(self):
        score = _game_score(score_accuracy=99, score_overall_difficulty=10.5)
        assert task_registry["high_acc_high_od"].check(score, {"min_accuracy": 98})

    def test_fc_above_ar_10(self):
        score = _game_score(score_perfect=True, score_approach_rate=11)
        assert task_registry["fc_above_ar_10"].check(score, {})

    def test_clear_famous_map(self):
        score = _game_score(beatmap_id=942356)
        assert task_registry["clear_famous_map"].check(score, {"map_id": 942356})

    def test_hdfl(self):
        score = _game_score(score_mods_json={"HD": {}, "FL": {}})
        assert task_registry["hdfl"].check(score, {})

    def test_stars_above(self):
        score = _game_score(score_difficulty_total=7.0)
        assert task_registry["stars_above"].check(score, {"min_stars": 6})

    def test_pp_above(self):
        score = _game_score(score_performance_total=500)
        assert task_registry["pp_above"].check(score, {"min_pp": 400})
