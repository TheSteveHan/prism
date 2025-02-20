from django.apps import AppConfig


class UserApppConfig(AppConfig):
   name = 'user'

   def ready(self):
       import user.signals  # noqa
