# Generated by Django 4.0.6 on 2022-07-27 16:06

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("leaderboards", "0016_leaderboard_notification_discord_webhook_url"),
    ]

    operations = [
        migrations.AlterField(
            model_name="leaderboard",
            name="member_count",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
