from django.db import models
from enum import IntEnum
from django.contrib.auth import get_user_model


# Create your models here.
class StripeCustomer(models.Model):
    user = models.OneToOneField(to=get_user_model(), on_delete=models.SET_NULL, null=True)
    customer_id = models.TextField()
    subscription_id = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.user.username


class LicensePurchase(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    customer_id = models.TextField(null=True)
    payment_id = models.TextField(null=True)
    purchase_time = models.DateField(auto_now_add=True)
    expiration_time = models.DateField()

    def __str__(self):
        return self.user.username

class StripeConnectAccountType(IntEnum):
    STANDARD = 1
    EXPRESS = 2

# Create your models here.
class StripeConnectAccount(models.Model):
    user_id = models.TextField(db_index=True, blank=True)
    ac_id = models.TextField(null=True, blank=True)
    account_id = models.TextField()
    account_type = models.IntegerField()
    info = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.user_id
