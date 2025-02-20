# Generated by Django 3.1.7 on 2022-04-04 17:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_auto_20210501_1625'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='campaign',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='http_referer',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='invite_code',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='referrer',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='CampaignEmailRecord',
            fields=[
                ('record_id', models.CharField(max_length=12, primary_key=True, serialize=False, unique=True)),
                ('user_id', models.TextField()),
                ('campaign_id', models.TextField()),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'unique_together': {('user_id', 'campaign_id')},
            },
        ),
    ]
