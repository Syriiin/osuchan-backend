from datetime import datetime

from minigames.games import GameScore


def _game_score(id=1, player_id=1, team_id=1, score_id=1, score_accuracy=0.0, **kwargs):
    fields = dict(
        id=id,
        player_id=player_id,
        team_id=team_id,
        score_id=score_id,
        points=0,
        score_score=0,
        score_count_300=0,
        score_count_100=0,
        score_count_50=0,
        score_count_miss=0,
        score_best_combo=0,
        score_perfect=False,
        score_mods_json={},
        score_accuracy=score_accuracy,
        score_rank="A",
        score_date=datetime(2026, 1, 1, 12, 0, 0),
        beatmap_id=1,
        beatmap_creator_name="m",
        beatmap_status=1,
        beatmap_title="",
        beatmap_artist="",
        beatmap_difficulty_name="",
        beatmap_approval_date=None,
        beatmap_hitobject_counts={},
        score_bpm=0,
        score_length=0,
        score_overall_difficulty=0,
        score_approach_rate=0,
        score_performance_total=None,
        score_difficulty_total=None,
    )
    fields.update(kwargs)
    return GameScore(**fields)
