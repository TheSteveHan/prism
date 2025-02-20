from django.core.mail.backends.smtp import EmailBackend as SmtpBackend
from django.core.mail.backends.console import EmailBackend as ConsoleBackend
import logging
import os
logger = logging.getLogger(__name__)  # or you could enter a specific logger name
logger.setLevel(logging.DEBUG)

BASE_EMAIL_BACKEND = (
    SmtpBackend
    if os.environ.get('SMTP_PASSWORD')
    else ConsoleBackend
)

class ActivationMiddleWare:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # activate user if applicable
        if request.user and request.user.is_authenticated and request.user.deactivated_at is not None:
            request.user.deactivated_at = None
            request.user.save()
        response = self.get_response(request)
        return response

class LoggingEmailBackend(BASE_EMAIL_BACKEND):
  def send_messages(self, email_messages):
    try:
        for msg in email_messages:
            print(f"Sending message '{msg.subject}' to recipients: {msg.to}")
            if os.environ.get('LOG_EMAIL_CONTENT'):
                print(f"with content: \n{msg.message()}\n\n")
    except:
        print("Problem logging recipients, ignoring")

    result = super(LoggingEmailBackend, self).send_messages(email_messages)
    print(f"Result of message '{msg.subject}' to recipients: {msg.to}: {result}")
    return result
