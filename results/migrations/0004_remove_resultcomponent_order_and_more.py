# Generated by Django 5.0.6 on 2024-12-06 12:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('results', '0003_resultcomponent_subject'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resultcomponent',
            name='order',
        ),
        migrations.AddField(
            model_name='resultcomponent',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
