# Generated by Django 3.2 on 2022-04-03 07:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0008_auto_20220403_0406'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountsettings',
            name='comment_notifications',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='accountsettings',
            name='friend_request_notifications',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='accountsettings',
            name='group_message_notifications',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='accountsettings',
            name='like_notifications',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='accountsettings',
            name='message_notifications',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='accountsettings',
            name='push_notifications',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='accountsettings',
            name='friendship',
            field=models.CharField(choices=[('Anyone', 'Anyone'), ('Mutual Friends', 'Mutual Friends'), ('Friends', 'Friends')], default='Friends', max_length=20, verbose_name='friendship'),
        ),
        migrations.AlterField(
            model_name='accountsettings',
            name='private_chat_perm',
            field=models.CharField(choices=[('Anyone', 'Anyone'), ('Mutual Friends', 'Mutual Friends'), ('Friends', 'Friends')], default='Friends', max_length=20, verbose_name='private_chat_perm'),
        ),
        migrations.AlterField(
            model_name='accountsettings',
            name='public_chat_perm',
            field=models.CharField(choices=[('Anyone', 'Anyone'), ('Friends', 'Friends'), ('No One', 'No One')], default='Friends', max_length=10, verbose_name='public_chat_perm'),
        ),
    ]