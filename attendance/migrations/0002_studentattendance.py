# Generated by Django 5.0.6 on 2024-12-01 13:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0002_session_school_and_more'),
        ('attendance', '0001_initial'),
        ('classes', '0015_teacherclassassignment'),
        ('schools', '0004_branch_schools_bra_branch__6b913a_idx_and_more'),
        ('students', '0007_student_guardians'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentAttendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attendance_count', models.PositiveIntegerField(blank=True, default=0, null=True)),
                ('date', models.DateField(auto_now_add=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('branch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='attendance_records', to='schools.branch')),
                ('session', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='attendance_records', to='academics.session')),
                ('student', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='attendance_records', to='students.student')),
                ('student_class', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='attendance_records', to='classes.class')),
                ('term', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='attendance_records', to='academics.term')),
            ],
            options={
                'indexes': [models.Index(fields=['session', 'term', 'branch', 'student_class', 'student', 'date'], name='attendance__session_dd5555_idx')],
                'unique_together': {('session', 'term', 'branch', 'student_class', 'student', 'date')},
            },
        ),
    ]
