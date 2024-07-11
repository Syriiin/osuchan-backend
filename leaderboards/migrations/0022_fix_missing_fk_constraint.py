# Generated by Django 4.2.13 on 2024-07-11 13:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0020_remove_score_profiles_sc_perform_b4b2d6_idx_and_more"),
        ("leaderboards", "0021_membership_unique_memberships"),
    ]

    operations = [
        migrations.AlterField(
            model_name="membershipscore",
            name="membership",
            field=models.ForeignKey(
                db_constraint=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="membership_scores",
                to="leaderboards.membership",
            ),
        ),
        migrations.AlterField(
            model_name="membershipscore",
            name="score",
            field=models.ForeignKey(
                db_constraint=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="membership_scores",
                to="profiles.score",
            ),
        ),
        migrations.AlterField(
            model_name="membershipscore",
            name="membership",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="membership_scores",
                to="leaderboards.membership",
            ),
        ),
        migrations.AlterField(
            model_name="membershipscore",
            name="score",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="membership_scores",
                to="profiles.score",
            ),
        ),
    ]
