# Generated by Django 3.2 on 2022-04-03 12:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0008_alter_comment_reply'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='reply',
        ),
        migrations.AddField(
            model_name='comment',
            name='reply_obj',
            field=models.BooleanField(blank=True, null=True, verbose_name='reply_obj'),
        ),
    ]
