# Generated by Django 3.1.7 on 2021-03-03 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stripe_payment", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="stripecustomer",
            name="stripeCustomerId",
        ),
        migrations.RemoveField(
            model_name="stripecustomer",
            name="stripeSubscriptionId",
        ),
        migrations.AddField(
            model_name="stripecustomer",
            name="customer_id",
            field=models.TextField(),
        ),
        migrations.AddField(
            model_name="stripecustomer",
            name="subscription_id",
            field=models.TextField(),
        ),
    ]
