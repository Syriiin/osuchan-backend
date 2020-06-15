# Generated by Django 3.0 on 2020-03-30 13:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0010_scorefilter'),
        ('leaderboards', '0009_auto_20200328_1242'),
    ]

    operations = [
        migrations.AlterField(
            model_name='leaderboard',
            name='score_filter',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='profiles.ScoreFilter'),
        ),
    ]