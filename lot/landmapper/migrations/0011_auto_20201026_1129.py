# Generated by Django 2.2.12 on 2020-10-26 11:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('landmapper', '0010_auto_20201005_1653'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taxlot',
            name='elev_max',
        ),
        migrations.RemoveField(
            model_name='taxlot',
            name='elev_max_1',
        ),
        migrations.RemoveField(
            model_name='taxlot',
            name='elev_min',
        ),
        migrations.RemoveField(
            model_name='taxlot',
            name='elev_min_1',
        ),
        migrations.AddField(
            model_name='taxlot',
            name='area',
            field=models.FloatField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='taxlot',
            name='rangedir',
            field=models.CharField(blank=True, default=None, max_length=3, null=True),
        ),
        migrations.AddField(
            model_name='taxlot',
            name='twnshpdir',
            field=models.CharField(blank=True, default=None, max_length=3, null=True),
        ),
        migrations.AddField(
            model_name='taxlot',
            name='twnshplab',
            field=models.CharField(blank=True, default=None, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='taxlot',
            name='acres',
            field=models.FloatField(blank=True, default=None, null=True),
        ),
    ]
