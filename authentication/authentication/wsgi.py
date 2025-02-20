"""
WSGI config for authentication project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
import time
import threading

from django.core.wsgi import get_wsgi_application
from .waffles import config_waffles
import logging
logging.basicConfig()


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'authentication.settings')

application = get_wsgi_application()


config_waffles()

def start_drip_cron():
    # pause for other pods to die off before starting to prevent double send issue
    # TODO use a proper lock
    time.sleep(60)
    from drip.scheduler.cron_scheduler import cron_send_drips
    cron_send_drips()

if os.getenv("SEND_DRIP"):
    threading.Thread(target=start_drip_cron).start()
