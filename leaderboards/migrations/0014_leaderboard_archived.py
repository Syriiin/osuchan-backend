# Generated by Django 3.0.7 on 2020-07-19 09:08

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("leaderboards", "0013_auto_20200620_1935"),
    ]

    operations = [
        migrations.AddField(
            model_name="leaderboard",
            name="archived",
            field=models.BooleanField(default=False),
        ),
    ]
