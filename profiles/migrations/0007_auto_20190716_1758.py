# Generated by Django 2.2.3 on 2019-07-16 07:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0006_auto_20190710_2235"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="score",
            index=models.Index(fields=["pp"], name="profiles_sc_pp_840a93_idx"),
        ),
    ]
