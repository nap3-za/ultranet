# Generated by Django 3.2 on 2022-04-03 04:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('friend', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='friendrequest',
            name='is_active',
        ),
    ]
