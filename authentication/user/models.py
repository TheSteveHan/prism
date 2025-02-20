import random
import string
from uuid import uuid4
from django.contrib.auth.models import AbstractUser
from django.db import models
from user.growthbook import get_feature_value
from django.utils import timezone


def get_rand_string(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

class CustomUser(AbstractUser):
    uuid = models.UUIDField(unique=True, default=uuid4)
    jwt_version = models.UUIDField(default=uuid4)
    phone_number = models.fields.CharField(max_length=20, default='', null=True, blank=True)
    first_name = models.fields.CharField(max_length=20, default='', null=True, blank=True)
    referrer = models.ForeignKey("self", on_delete=models.SET_NULL, default=None, null=True, blank=True)
    http_referer = models.TextField(null=True, blank=True)
    campaign = models.TextField(null=True, blank=True)
    invite_code = models.TextField(null=True, blank=True)
    unsubscribed = models.BooleanField(null=True, default=False)
    deactivated_at = models.DateTimeField(null=True, default=None, blank=True)


    def set_invite_code(self):
        """create an invite code for a given user"""
        if not self.invite_code:
            new_invite_code = uuid4().hex[:6]
            while CustomUser.objects.filter(invite_code=new_invite_code).first():
                logger.error("Invite code UUID collision")
                new_invite_code = uuid4().hex[:6]
            self.invite_code = new_invite_code


    def get_contact_email():
        """Return the primary email or the first verified email or the first email"""
        all_emails = self.emailaddress_set.all()
        verified_emails = [e for e in all_emails if e.verified]
        primary_email = None
        for email in all_emails:
            if email.primary:
                primary_email = email
        # if primary email exists and is verified or no verified email exists
        if primary_email and primary_email.verified or (not verified_emails):
            return primary_email.email
        if verified_emails:
            return verified_emails[0]
        if all_emails:
            return all_emails[0]
        return None

    # user specific, customizable values (there is probably a better way to do this)
    @property
    def advice_email_subject(self):
        idx = get_feature_value(self, 'aes1', 0)
        subjects = [
            "Your Advice?",
            "🤔Your Advice?",
            "Your Advice?🤔",
            "What's Your Advice?",
            "🤔What's Your Advice?",
            "What's Your Advice?🤔",
        ]
        return subjects[min(idx, len(subjects)-1)]

class CampaignEmailRecord(models.Model):
    record_id = models.CharField(max_length=12, primary_key=True, unique=True, null=False)
    user_id = models.TextField(null=False)
    campaign_id = models.TextField(null=False)
    timestamp = models.DateTimeField(default=timezone.now)
    opened = models.DateTimeField(null=True)
    open_headers = models.JSONField(null=True)

    def set_record_id(self):
        if not self.record_id:
            new_record_id = get_rand_string(8)
            while CampaignEmailRecord.objects.filter(record_id=new_record_id).first():
                logger.error("record_id UUID collision")
                new_record_id = get_rand_string(8)
            self.record_id = new_record_id

    class Meta:
        unique_together = ['user_id', 'campaign_id']
