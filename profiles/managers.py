from django.db import models
from django.apps import apps

from datetime import datetime
import pytz

from common.osu import apiv1
from common.osu.enums import BeatmapStatus

class OsuUserManager(models.Manager):
    def non_restricted(self):
        return self.get_queryset().filter(disabled=False)

    def create_or_update(self, user_id, gamemode):
        # fetch user data
        data = apiv1.get_user(user_id, gamemode)

        # get or create OsuUser model
        try:
            osu_user = self.model.objects.get(id=user_id)
            if not data:
                # user restricted probably
                osu_user.disabled = True
                osu_user.save()
                return None
        except self.model.DoesNotExist:
            osu_user = self.model(id=user_id)

        # update fields
        osu_user.username = data["username"]
        osu_user.country = data["country"]
        osu_user.join_date = datetime.strptime(data["join_date"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.UTC)
        osu_user.disabled = False

        # save and return OsuUser model
        osu_user.save()

        # need to get model via apps to avoid circular import
        user_stats_model = apps.get_model("profiles.UserStats")
        user_stats = user_stats_model.objects.create_or_update_from_data(data, gamemode)
        # osu_user is saved before stats so it can be referenced as a foreign key
        osu_user.stats.add(user_stats, bulk=True)

        return osu_user

class UserStatsManager(models.Manager):
    def non_restricted(self):
        return self.get_queryset().filter(user__disabled=False)

    def create_or_update_from_data(self, user_data, gamemode):
        # add user_data from passed deserialised osu! api response dict
        # gamemode required as parameter because osu! api doesn't return the mode you queried for
        # get or create UserStats model
        try:
            user_stats = self.model.objects.get(user_id=user_data["user_id"], gamemode=gamemode)
        except self.model.DoesNotExist:
            user_stats = self.model(user_id=user_data["user_id"])
            user_stats.gamemode = gamemode

        # update fields
        user_stats.playcount = int(user_data["playcount"])
        user_stats.playtime = int(user_data["total_seconds_played"])
        user_stats.level = float(user_data["level"])
        user_stats.ranked_score = int(user_data["ranked_score"])
        user_stats.total_score = int(user_data["total_score"])
        user_stats.rank = int(user_data["pp_rank"])
        user_stats.country_rank = int(user_data["pp_country_rank"])
        user_stats.pp = float(user_data["pp_raw"])
        user_stats.accuracy = float(user_data["accuracy"])
        user_stats.count_300 = int(user_data["count300"])
        user_stats.count_100 = int(user_data["count100"])
        user_stats.count_50 = int(user_data["count50"])
        user_stats.count_rank_ss = int(user_data["count_rank_ss"])
        user_stats.count_rank_ssh = int(user_data["count_rank_ssh"])
        user_stats.count_rank_s = int(user_data["count_rank_s"])
        user_stats.count_rank_sh = int(user_data["count_rank_sh"])
        user_stats.count_rank_a = int(user_data["count_rank_a"])

        user_stats.save()

        # need to get model via apps to avoid circular import
        score_model = apps.get_model("profiles.Score")
        scores = score_model.objects.create_or_update_from_data(apiv1.get_user_best(user_stats.user_id, gamemode=gamemode, limit=100), user_stats.id)
        user_stats.scores.add(*scores, bulk=True)

        # kinda annoying and inefficient that we need to resave the model once we get to this point but we need to unless we want to remove the db constrain on scores requiring a user_stats since insertion
        user_stats.process_pp_totals()
        user_stats.save()

        return user_stats

class BeatmapManager(models.Manager):
    def create_or_update(self, beatmap_id):
        # get or create Beatmap model
        try:
            beatmap = self.model.objects.get(id=beatmap_id)
        except self.model.DoesNotExist:
            beatmap = self.model(id=beatmap_id)
        
        if beatmap.status not in (BeatmapStatus.RANKED, BeatmapStatus.APPROVED):
            # fetch beatmap data if not in database and ranked/approved
            data = apiv1.get_beatmaps(beatmap_id=beatmap_id)[0]
            
            # update fields
            beatmap.set_id = int(data["beatmapset_id"])
            beatmap.artist = data["artist"]
            beatmap.title = data["title"]
            beatmap.difficulty_name = data["version"]
            beatmap.gamemode = int(data["mode"])
            beatmap.status = int(data["approved"])
            beatmap.creator_name = data["creator"]
            beatmap.bpm = float(data["bpm"])
            beatmap.max_combo = int(data["max_combo"]) if data["max_combo"] != None else None
            beatmap.drain_time = int(data["hit_length"])
            beatmap.total_time = int(data["total_length"])
            beatmap.circle_size = float(data["diff_size"])
            beatmap.overall_difficulty = float(data["diff_overall"])
            beatmap.approach_rate = float(data["diff_approach"])
            beatmap.health_drain = float(data["diff_drain"])
            beatmap.star_rating = float(data["difficultyrating"])
            beatmap.last_updated = datetime.strptime(data["last_update"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.UTC)
            
            # foreign key ids
            beatmap.creator_id = int(data["creator_id"])

        # save and return Beatmap model
        beatmap.save()
        return beatmap

class ScoreManager(models.Manager):
    def non_restricted(self):
        return self.get_queryset().filter(user_stats__user__disabled=False)

    def create_or_update(self, beatmap_id, user_id):
        # fetch scores for player on a beatmap
        data = apiv1.get_scores(beatmap_id=beatmap_id, user_id=user_id)
        return self.create_or_update_from_data(data)

    def create_or_update_from_data(self, score_data_list, user_stats_id):
        # add list of scores from passed deserialised osu! api response (dicts)
        scores = []

        # need to get model via apps to avoid circular import
        beatmap_model = apps.get_model("profiles.Beatmap")
        
        for score_data in score_data_list:
            # get or create Score model
            try:
                # TODO: check if this foreign key lookup for user_id has a large impact (probably doesnt because of indexes)
                score = self.model.objects.get(user_stats__user_id=int(score_data["user_id"]), beatmap_id=int(score_data["beatmap_id"]), mods=int(score_data["enabled_mods"]))
            except self.model.DoesNotExist:
                score = self.model()
            
            # update fields
            score.score = int(score_data["score"])
            score.count_300 = int(score_data["count300"])
            score.count_100 = int(score_data["count100"])
            score.count_50 = int(score_data["count50"])
            score.count_miss = int(score_data["countmiss"])
            score.count_geki = int(score_data["countgeki"])
            score.count_katu = int(score_data["countkatu"])
            score.best_combo = int(score_data["maxcombo"])
            score.perfect = bool(int(score_data["perfect"]))
            score.mods = int(score_data["enabled_mods"])
            score.rank = score_data["rank"]
            score.pp = float(score_data["pp"])
            score.date = datetime.strptime(score_data["date"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.UTC)

            # foreign keys
            beatmap = beatmap_model.objects.create_or_update(score_data["beatmap_id"])
            score.beatmap = beatmap
            score.user_stats_id = user_stats_id

            # not using bulk queries because they dont call .save() and we need that for oppai calcs
            score.save()
            scores.append(score)

        return scores
