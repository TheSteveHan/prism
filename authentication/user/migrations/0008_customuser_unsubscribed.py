# Generated by Django 3.1.7 on 2022-04-14 00:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0007_campaignemailrecord_open_headers'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='unsubscribed',
            field=models.BooleanField(default=False, null=True),
        ),
    ]
