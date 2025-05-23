# Generated by Django 5.1.4 on 2024-12-21 05:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0026_scorefilter_disqualified_mods_json_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="scorefilter",
            name="disqualified_mods_json",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name="scorefilter",
            name="required_mods_json",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
