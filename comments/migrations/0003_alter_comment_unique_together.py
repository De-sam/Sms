# Generated by Django 5.0.6 on 2024-12-19 20:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('comments', '0002_alter_comment_unique_together'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='comment',
            unique_together=set(),
        ),
    ]
