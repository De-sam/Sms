# Generated by Django 5.0.6 on 2024-12-03 16:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ratings', '0002_remove_behavioralrating_comments_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='psychomotorrating',
            old_name='music',
            new_name='artistry',
        ),
        migrations.AddField(
            model_name='behavioralrating',
            name='emotional_stability',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='behavioralrating',
            name='teamwork',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='psychomotorrating',
            name='games',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='psychomotorrating',
            name='verbal_fluency',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]