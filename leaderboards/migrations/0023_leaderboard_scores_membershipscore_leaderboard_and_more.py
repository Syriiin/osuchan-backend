# Generated by Django 4.2.13 on 2024-07-14 09:48

import django.db.models.deletion
from django.db import migrations, models


def set_leaderboard_id(apps, schema_editor):
    MembershipScore = apps.get_model("leaderboards", "MembershipScore")
    Membership = apps.get_model("leaderboards", "Membership")
    MembershipScore.objects.update(
        leaderboard_id=models.Subquery(
            Membership.objects.filter(id=models.OuterRef("membership_id")).values(
                "leaderboard_id"
            )[:1]
        )
    )


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0020_remove_score_profiles_sc_perform_b4b2d6_idx_and_more"),
        ("leaderboards", "0022_fix_missing_fk_constraint"),
    ]

    operations = [
        migrations.AddField(
            model_name="leaderboard",
            name="scores",
            field=models.ManyToManyField(
                related_name="leaderboards",
                through="leaderboards.MembershipScore",
                to="profiles.score",
            ),
        ),
        migrations.AddField(
            model_name="membershipscore",
            name="leaderboard",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="leaderboards.leaderboard",
            ),
            preserve_default=False,
        ),
        migrations.RunPython(set_leaderboard_id, migrations.RunPython.noop),
        migrations.AddIndex(
            model_name="membershipscore",
            index=models.Index(
                fields=["leaderboard", "performance_total"],
                name="leaderboard_leaderb_909991_idx",
            ),
        ),
    ]