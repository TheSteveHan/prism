from django.db.models.signals import post_save
from django.dispatch import receiver

from django.core.mail import send_mail
from django.conf import settings
from user.models import CustomUser

if settings.ADMIN_EMAILS:
    @receiver(post_save, sender=CustomUser)
    def send_email_to_admin(sender, instance, created, **kwargs):
        if created:
            send_mail(
                'New member sign up!'.format(instance.email),
                '{} just signed up'.format(instance.email),
                settings.DEFAULT_FROM_EMAIL,
                settings.ADMIN_EMAILS,
                fail_silently=False,
            )
