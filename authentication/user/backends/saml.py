from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .base import BaseBackend


class SAMLBackend(BaseBackend):

    def authenticate(self, request, saml_authentication=None):
        if not saml_authentication:  # Using another authentication method
            return None

        if saml_authentication.is_authenticated():
            attributes = saml_authentication.get_attributes()
            import pdb;pdb.set_trace()
            user_model = get_user_model()
            email = saml_authentication.get_nameid()
            try:
                validate_email(email)
            except ValidationError as e:
                raise "Invalid SAML configuration. Expected nameid to be email"
            try:
                user = user_model.objects.get(email=email)
            except user_model.DoesNotExist:
                user = user_model(email=email)
                user.set_unusable_password()
                user.first_name = attributes['firstName'][0]
                user.last_name = attributes['lastName'][0]
                user.email = email
                user.save()
                # TODO add user to groups base on roles
            return user
        return None
