# Generated by Django 3.2 on 2022-04-03 12:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='choice',
            name='is_active',
        ),
        migrations.RemoveField(
            model_name='comment',
            name='is_active',
        ),
        migrations.RemoveField(
            model_name='comment',
            name='is_reply',
        ),
        migrations.RemoveField(
            model_name='comment',
            name='replies',
        ),
        migrations.RemoveField(
            model_name='content',
            name='is_active',
        ),
        migrations.RemoveField(
            model_name='content',
            name='kind',
        ),
        migrations.AddField(
            model_name='comment',
            name='reply',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reply_obj', to='blog.comment'),
        ),
        migrations.AddField(
            model_name='content',
            name='content_type',
            field=models.CharField(choices=[('Post', 'Post'), ('Poll', 'Poll')], default='default', max_length=50, verbose_name='content_type'),
        ),
    ]
