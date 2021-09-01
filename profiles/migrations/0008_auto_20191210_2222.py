# Generated by Django 2.2.3 on 2019-12-10 11:22

import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0007_auto_20190716_1758"),
    ]

    operations = [
        migrations.AddField(
            model_name="beatmap",
            name="approval_date",
            field=models.DateTimeField(
                default=datetime.datetime(
                    1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc
                )
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="beatmap",
            name="submission_date",
            field=models.DateTimeField(
                default=datetime.datetime(
                    1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc
                )
            ),
            preserve_default=False,
        ),
    ]
