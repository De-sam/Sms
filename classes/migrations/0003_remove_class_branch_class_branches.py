# Generated by Django 5.0.6 on 2024-08-03 08:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('classes', '0002_alter_class_branch'),
        ('schools', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='class',
            name='branch',
        ),
        migrations.AddField(
            model_name='class',
            name='branches',
            field=models.ManyToManyField(blank=True, related_name='classes', to='schools.branch'),
        ),
    ]