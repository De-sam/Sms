# Generated by Django 5.0.6 on 2024-08-07 21:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('classes', '0006_subject_all_levels_alter_subject_level'),
        ('schools', '0003_remove_branch_classes'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubjectType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.RenameField(
            model_name='subject',
            old_name='all_levels',
            new_name='is_general',
        ),
        migrations.RemoveField(
            model_name='class',
            name='subjects',
        ),
        migrations.RemoveField(
            model_name='subject',
            name='base_code',
        ),
        migrations.RemoveField(
            model_name='subject',
            name='code',
        ),
        migrations.RemoveField(
            model_name='subject',
            name='level',
        ),
        migrations.AddField(
            model_name='class',
            name='branches',
            field=models.ManyToManyField(blank=True, related_name='classes', to='schools.branch'),
        ),
        migrations.AddField(
            model_name='subject',
            name='classes',
            field=models.ManyToManyField(blank=True, related_name='subjects', to='classes.class'),
        ),
        migrations.AddField(
            model_name='subject',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='class',
            name='level',
            field=models.CharField(choices=[('primary', 'Primary'), ('junior_secondary', 'Junior Secondary'), ('senior_secondary', 'Senior Secondary')], max_length=20),
        ),
        migrations.AlterField(
            model_name='subject',
            name='department',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='classes.department'),
        ),
        migrations.AlterField(
            model_name='subject',
            name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AddField(
            model_name='subject',
            name='subject_type',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='classes.subjecttype'),
            preserve_default=False,
        ),
    ]