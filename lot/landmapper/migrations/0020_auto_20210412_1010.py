# Generated by Django 2.2.12 on 2021-04-12 10:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('landmapper', '0019_property_property_map_image_509x722'),
    ]

    operations = [
        migrations.RenameField(
            model_name='property',
            old_name='property_map_image_509x722',
            new_name='property_map_image_alt',
        ),
    ]
