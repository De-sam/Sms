# Generated by Django 5.0.6 on 2024-12-02 22:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ratings', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='behavioralrating',
            name='comments',
        ),
        migrations.RemoveField(
            model_name='psychomotorrating',
            name='comments',
        ),
    ]
