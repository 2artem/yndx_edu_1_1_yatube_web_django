# Generated by Django 2.2.6 on 2022-01-13 14:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0009_group_new_field'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='group',
            name='new_field',
        ),
    ]