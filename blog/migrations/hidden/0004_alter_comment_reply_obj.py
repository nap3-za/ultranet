# Generated by Django 3.2 on 2022-04-03 12:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0003_auto_20220403_0406'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='reply_obj',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='_reply_obj', to='blog.comment'),
        ),
    ]