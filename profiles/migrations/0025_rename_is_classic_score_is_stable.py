# Generated by Django 5.1.3 on 2024-11-30 04:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0024_score_mods_json"),
    ]

    operations = [
        migrations.RenameField(
            model_name="score",
            old_name="is_classic",
            new_name="is_stable",
        ),
    ]
