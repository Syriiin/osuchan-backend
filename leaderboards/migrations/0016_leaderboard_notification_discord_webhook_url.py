# Generated by Django 4.0.6 on 2022-07-27 10:38

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("leaderboards", "0015_auto_20210614_0706"),
    ]

    operations = [
        migrations.AddField(
            model_name="leaderboard",
            name="notification_discord_webhook_url",
            field=models.CharField(blank=True, max_length=250),
        ),
    ]
