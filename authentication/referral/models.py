from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.
REFERRAL_STATUS_FREE = "FREE"
REFERRAL_STATUS_ACTIVE = "ACTIVE"
REFERRAL_STATUS_CANCELED = "CANCELED"


class Lead(models.Model):
    affiliate = models.ForeignKey(to=get_user_model(), on_delete=models.SET_NULL, null=True, related_name="leads")
    session_id = models.TextField(null=True, unique=True)
    source = models.TextField(null=True)
    destination = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Referral(models.Model):
    user = models.OneToOneField(to=get_user_model(), on_delete=models.SET_NULL, null=True)
    affiliate = models.ForeignKey(to=get_user_model(), on_delete=models.SET_NULL, null=True, related_name="referrals")
    status = models.TextField(null=True)  # Free, Active, Canceled, Other
    init_commission = models.FloatField(default=0)
    recurring_commission = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Commission(models.Model):
    user = models.ForeignKey(to=get_user_model(), on_delete=models.SET_NULL, null=True)
    affiliate = models.ForeignKey(to=get_user_model(), on_delete=models.SET_NULL, null=True, related_name="commissions")
    status = models.TextField(null=True)
    revenue = models.FloatField(default=0)
    commission = models.FloatField(default=0)
    event_id = models.TextField(null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Payout(models.Model):
    affiliate = models.ForeignKey(to=get_user_model(), on_delete=models.SET_NULL, null=True, related_name="payouts")
    email = models.TextField()
    status = models.TextField(null=True)
    amount = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PayoutSettings(models.Model):
    affiliate = models.OneToOneField(to=get_user_model(), on_delete=models.SET_NULL, null=True)
    email = models.EmailField()
