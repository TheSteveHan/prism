# Generated by Django 3.1.7 on 2021-05-03 13:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("referral", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="commission",
            old_name="affliate",
            new_name="affiliate",
        ),
        migrations.RenameField(
            model_name="lead",
            old_name="affliate",
            new_name="affiliate",
        ),
        migrations.RenameField(
            model_name="payout",
            old_name="affliate",
            new_name="affiliate",
        ),
        migrations.RenameField(
            model_name="payoutsettings",
            old_name="affliate",
            new_name="affiliate",
        ),
        migrations.RenameField(
            model_name="referral",
            old_name="affliate",
            new_name="affiliate",
        ),
        migrations.RemoveField(
            model_name="lead",
            name="click",
        ),
        migrations.RemoveField(
            model_name="lead",
            name="updated_at",
        ),
        migrations.AlterField(
            model_name="commission",
            name="id",
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
        ),
        migrations.AlterField(
            model_name="lead",
            name="id",
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
        ),
        migrations.AlterField(
            model_name="payout",
            name="id",
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
        ),
        migrations.AlterField(
            model_name="payoutsettings",
            name="id",
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
        ),
        migrations.AlterField(
            model_name="referral",
            name="id",
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
        ),
    ]
