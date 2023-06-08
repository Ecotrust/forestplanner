# Generated by Django 4.2.2 on 2023-06-08 09:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
        ('landmapper', '0029_merge_0028_auto_20230228_1025_0028_person'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='type_other',
            field=models.CharField(blank=True, default=None, max_length=255, null=True, verbose_name='Other primary use:'),
        ),
        migrations.AlterField(
            model_name='property',
            name='content_type',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='%(app_label)s_%(class)s_related', to='contenttypes.contenttype'),
        ),
        migrations.AlterField(
            model_name='property',
            name='sharing_groups',
            field=models.ManyToManyField(blank=True, editable=False, related_name='%(app_label)s_%(class)s_related', to='auth.group', verbose_name='Share with the following groups'),
        ),
        migrations.AlterField(
            model_name='property',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(app_label)s_%(class)s_related', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='propertyrecord',
            name='content_type',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='%(app_label)s_%(class)s_related', to='contenttypes.contenttype'),
        ),
        migrations.AlterField(
            model_name='propertyrecord',
            name='sharing_groups',
            field=models.ManyToManyField(blank=True, editable=False, related_name='%(app_label)s_%(class)s_related', to='auth.group', verbose_name='Share with the following groups'),
        ),
        migrations.AlterField(
            model_name='propertyrecord',
            name='user',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(app_label)s_%(class)s_related', to=settings.AUTH_USER_MODEL),
        ),
    ]
