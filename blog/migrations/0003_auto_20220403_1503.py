# Generated by Django 3.2 on 2022-04-03 15:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0002_auto_20220403_1239'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='visibility',
        ),
        migrations.AlterField(
            model_name='comment',
            name='text',
            field=models.CharField(blank=True, max_length=750, verbose_name='text'),
        ),
    ]
