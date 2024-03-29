# Generated by Django 2.2.3 on 2019-07-17 22:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("osuauth", "0002_user_is_beta_tester"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="osu_user",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="profiles.OsuUser",
            ),
        ),
    ]
