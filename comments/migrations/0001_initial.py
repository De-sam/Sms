# Generated by Django 5.0.6 on 2024-12-05 18:28

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('academics', '0002_session_school_and_more'),
        ('students', '0007_student_guardians'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment_text', models.TextField(help_text='The content of the comment.')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The date and time when the comment was created.')),
                ('author', models.ForeignKey(help_text='The user who wrote this comment.', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('session', models.ForeignKey(help_text='The academic session for this comment.', on_delete=django.db.models.deletion.CASCADE, to='academics.session')),
                ('student', models.ForeignKey(help_text='The student this comment is for.', on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='students.student')),
                ('term', models.ForeignKey(help_text='The term for this comment.', on_delete=django.db.models.deletion.CASCADE, to='academics.term')),
            ],
        ),
    ]
