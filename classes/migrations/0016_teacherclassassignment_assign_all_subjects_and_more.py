# Generated by Django 5.0.6 on 2024-12-03 12:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('classes', '0015_teacherclassassignment'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacherclassassignment',
            name='assign_all_subjects',
            field=models.BooleanField(default=False, help_text='Assign all subjects linked to the selected classes to the teacher.'),
        ),
        migrations.AlterField(
            model_name='teacherclassassignment',
            name='assigned_classes',
            field=models.ManyToManyField(blank=True, related_name='teacher_assignments', to='classes.class'),
        ),
    ]