# Generated by Django 5.0.6 on 2024-12-06 15:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('results', '0004_remove_resultcomponent_order_and_more'),
        ('schools', '0004_branch_schools_bra_branch__6b913a_idx_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studentresult',
            name='structure',
        ),
        migrations.RemoveField(
            model_name='studentresult',
            name='student',
        ),
        migrations.RemoveField(
            model_name='studentresult',
            name='subject',
        ),
        migrations.RemoveField(
            model_name='resultstructure',
            name='classes',
        ),
        migrations.RemoveField(
            model_name='resultstructure',
            name='session',
        ),
        migrations.RemoveField(
            model_name='resultstructure',
            name='term',
        ),
        migrations.AddField(
            model_name='resultcomponent',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='resultstructure',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AlterField(
            model_name='resultstructure',
            name='branch',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='result_structures', to='schools.branch'),
        ),
        migrations.DeleteModel(
            name='StudentComponentScore',
        ),
        migrations.DeleteModel(
            name='StudentResult',
        ),
    ]