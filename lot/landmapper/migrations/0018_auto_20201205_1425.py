# Generated by Django 2.2.12 on 2020-12-05 14:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('landmapper', '0017_auto_20201125_1059'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='context_scalebar_image',
            field=models.ImageField(null=True, upload_to=None),
        ),
        migrations.AddField(
            model_name='property',
            name='medium_scalebar_image',
            field=models.ImageField(null=True, upload_to=None),
        ),
    ]
