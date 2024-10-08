# Generated by Django 5.0.6 on 2024-08-19 14:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='staff',
            name='status',
            field=models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive')], default='active', max_length=10),
        ),
        migrations.AlterField(
            model_name='staff',
            name='cv',
            field=models.FileField(default=1, upload_to='cvs/'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='staff',
            name='staff_signature',
            field=models.FileField(default=1, upload_to='signatures/'),
            preserve_default=False,
        ),
    ]
