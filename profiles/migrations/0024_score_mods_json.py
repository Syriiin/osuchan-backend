# Generated by Django 5.1.3 on 2024-11-30 03:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0023_score_statistics"),
    ]

    operations = [
        migrations.AddField(
            model_name="score",
            name="mods_json",
            field=models.JSONField(default=[]),
            preserve_default=False,
        ),
    ]
