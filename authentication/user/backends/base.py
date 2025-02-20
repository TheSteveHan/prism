"""Base authentication backend for all 3rd party auth that we implement."""
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.contrib.auth import get_user_model

class BaseBackend:
    """Base class for authenticating a user"""
    def authenticate(self, request, **kwargs):
        """Authenticate and maybe create user."""
        username = self.get_username_from_credentials(request, **kwargs)
        if username is None:
            return None
        # get or create user if the credentials checkout
        user_model = get_user_model()
        try:
            user = user_model.objects.get(username=username)
        except user_model.DoesNotExist:
            # Create a new user. There's no need to set a password
            # because only the password from settings.py is checked.
            user = user_model(username=username)
            user.is_staff = False
            user.is_superuser = False
            user.save()
        return user

    def get_username_from_credentials(self, request, **kwargs):
        """Returns None to reject all by default."""
        return None

    def get_user(self, user_id):
        """Get user object based on user_id."""
        try:
            return get_user_model().objects.get(pk=user_id)
        except get_user_model().DoesNotExist:
            return None
