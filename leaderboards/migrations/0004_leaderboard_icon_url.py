# Generated by Django 2.2.3 on 2019-07-16 07:57

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("leaderboards", "0003_auto_20190712_1401"),
    ]

    operations = [
        migrations.AddField(
            model_name="leaderboard",
            name="icon_url",
            field=models.CharField(default="", max_length=250),
            preserve_default=False,
        ),
    ]
