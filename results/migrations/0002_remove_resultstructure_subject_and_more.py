# Generated by Django 5.0.6 on 2024-12-05 23:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0002_session_school_and_more'),
        ('classes', '0016_teacherclassassignment_assign_all_subjects_and_more'),
        ('results', '0001_initial'),
        ('schools', '0004_branch_schools_bra_branch__6b913a_idx_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resultstructure',
            name='subject',
        ),
        migrations.AddField(
            model_name='resultstructure',
            name='classes',
            field=models.ManyToManyField(blank=True, to='classes.class'),
        ),
        migrations.AddField(
            model_name='resultstructure',
            name='conversion_total',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='resultstructure',
            name='branch',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='schools.branch'),
        ),
        migrations.AlterField(
            model_name='resultstructure',
            name='ca_total',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='resultstructure',
            name='exam_total',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='resultstructure',
            name='session',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='academics.session'),
        ),
        migrations.AlterField(
            model_name='resultstructure',
            name='term',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='academics.term'),
        ),
    ]