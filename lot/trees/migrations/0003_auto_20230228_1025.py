# Generated by Django 3.2.14 on 2023-02-28 10:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trees', '0002_auto_20200429_1325'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scenario',
            name='input_rxs',
            field=models.JSONField(blank=True, default=dict, null=True, verbose_name='Prescriptions associated with each stand'),
        ),
        migrations.AlterField(
            model_name='scenario',
            name='output_scheduler_results',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='strata',
            name='stand_list',
            field=models.JSONField(),
        ),
    ]
