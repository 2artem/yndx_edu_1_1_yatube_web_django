# Generated by Django 2.2.6 on 2022-01-13 13:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0008_remove_post_t2t'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='new_field',
            field=models.CharField(default='SOME STRING', max_length=140),
        ),
    ]