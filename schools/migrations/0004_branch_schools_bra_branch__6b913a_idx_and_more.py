# Generated by Django 5.0.6 on 2024-09-06 19:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('landingpage', '0002_schoolregistration_landingpage_short_c_e4d8f6_idx_and_more'),
        ('schools', '0003_remove_branch_classes'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='branch',
            index=models.Index(fields=['branch_name'], name='schools_bra_branch__6b913a_idx'),
        ),
        migrations.AddIndex(
            model_name='branch',
            index=models.Index(fields=['school'], name='schools_bra_school__600b7d_idx'),
        ),
        migrations.AddIndex(
            model_name='branch',
            index=models.Index(fields=['primary_school'], name='schools_bra_primary_0a2a15_idx'),
        ),
        migrations.AddIndex(
            model_name='primaryschool',
            index=models.Index(fields=['school_name'], name='schools_pri_school__9f2288_idx'),
        ),
        migrations.AddIndex(
            model_name='primaryschool',
            index=models.Index(fields=['pry_school_id'], name='schools_pri_pry_sch_732cbb_idx'),
        ),
        migrations.AddIndex(
            model_name='primaryschool',
            index=models.Index(fields=['secondary_school'], name='schools_pri_seconda_1892fa_idx'),
        ),
    ]