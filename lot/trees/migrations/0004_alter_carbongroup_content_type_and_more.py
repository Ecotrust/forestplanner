# Generated by Django 4.2.2 on 2023-06-08 09:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
        ('trees', '0003_auto_20230228_1025'),
    ]

    operations = [
        migrations.AlterField(
            model_name='carbongroup',
            name='content_type',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='%(app_label)s_%(class)s_related', to='contenttypes.contenttype'),
        ),
        migrations.AlterField(
            model_name='carbongroup',
            name='sharing_groups',
            field=models.ManyToManyField(blank=True, editable=False, related_name='%(app_label)s_%(class)s_related', to='auth.group', verbose_name='Share with the following groups'),
        ),
        migrations.AlterField(
            model_name='carbongroup',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(app_label)s_%(class)s_related', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='forestproperty',
            name='content_type',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='%(app_label)s_%(class)s_related', to='contenttypes.contenttype'),
        ),
        migrations.AlterField(
            model_name='forestproperty',
            name='sharing_groups',
            field=models.ManyToManyField(blank=True, editable=False, related_name='%(app_label)s_%(class)s_related', to='auth.group', verbose_name='Share with the following groups'),
        ),
        migrations.AlterField(
            model_name='forestproperty',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(app_label)s_%(class)s_related', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='myrx',
            name='content_type',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='%(app_label)s_%(class)s_related', to='contenttypes.contenttype'),
        ),
        migrations.AlterField(
            model_name='myrx',
            name='sharing_groups',
            field=models.ManyToManyField(blank=True, editable=False, related_name='%(app_label)s_%(class)s_related', to='auth.group', verbose_name='Share with the following groups'),
        ),
        migrations.AlterField(
            model_name='myrx',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(app_label)s_%(class)s_related', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='scenario',
            name='content_type',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='%(app_label)s_%(class)s_related', to='contenttypes.contenttype'),
        ),
        migrations.AlterField(
            model_name='scenario',
            name='sharing_groups',
            field=models.ManyToManyField(blank=True, editable=False, related_name='%(app_label)s_%(class)s_related', to='auth.group', verbose_name='Share with the following groups'),
        ),
        migrations.AlterField(
            model_name='scenario',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(app_label)s_%(class)s_related', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='scenariostand',
            name='content_type',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='%(app_label)s_%(class)s_related', to='contenttypes.contenttype'),
        ),
        migrations.AlterField(
            model_name='scenariostand',
            name='sharing_groups',
            field=models.ManyToManyField(blank=True, editable=False, related_name='%(app_label)s_%(class)s_related', to='auth.group', verbose_name='Share with the following groups'),
        ),
        migrations.AlterField(
            model_name='scenariostand',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(app_label)s_%(class)s_related', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='stand',
            name='content_type',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='%(app_label)s_%(class)s_related', to='contenttypes.contenttype'),
        ),
        migrations.AlterField(
            model_name='stand',
            name='sharing_groups',
            field=models.ManyToManyField(blank=True, editable=False, related_name='%(app_label)s_%(class)s_related', to='auth.group', verbose_name='Share with the following groups'),
        ),
        migrations.AlterField(
            model_name='stand',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(app_label)s_%(class)s_related', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='strata',
            name='content_type',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='%(app_label)s_%(class)s_related', to='contenttypes.contenttype'),
        ),
        migrations.AlterField(
            model_name='strata',
            name='sharing_groups',
            field=models.ManyToManyField(blank=True, editable=False, related_name='%(app_label)s_%(class)s_related', to='auth.group', verbose_name='Share with the following groups'),
        ),
        migrations.AlterField(
            model_name='strata',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(app_label)s_%(class)s_related', to=settings.AUTH_USER_MODEL),
        ),
    ]