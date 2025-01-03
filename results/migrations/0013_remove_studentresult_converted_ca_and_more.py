# Generated by Django 5.0.6 on 2024-12-30 08:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('classes', '0016_teacherclassassignment_assign_all_subjects_and_more'),
        ('results', '0012_publishedresult_updated_at'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studentresult',
            name='converted_ca',
        ),
        migrations.RemoveField(
            model_name='studentresult',
            name='exam_score',
        ),
        migrations.RemoveField(
            model_name='studentresult',
            name='total_score',
        ),
        migrations.AddField(
            model_name='studentresult',
            name='subject',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='student_results', to='classes.subject'),
        ),
    ]
