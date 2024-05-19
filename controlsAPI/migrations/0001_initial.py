# Generated by Django 4.1.13 on 2024-05-19 20:46

import controlsAPI.models
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Control',
            fields=[
                ('name', models.TextField(primary_key=True, serialize=False, unique=True)),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='ControlSet',
            fields=[
                ('slug', models.TextField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.TextField(unique=True)),
                ('hierarchy_depth', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='ControlSetReference',
            fields=[
                ('reference_id', models.TextField(default=None, null=True)),
                ('name', models.TextField(primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='ControlHierarchy',
            fields=[
                ('slug', models.TextField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('parents', controlsAPI.models.ListField(default=['None'])),
                ('children', controlsAPI.models.ListField(default=['None'])),
                ('control_set', models.ManyToManyField(blank=True, default=controlsAPI.models.get_empty_queryset, related_name='control_hierarchies', to='controlsAPI.controlsetreference')),
            ],
        ),
    ]