from google.oauth2 import id_token
from google.auth.transport import requests
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.providers.apple.views import AppleOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.shortcuts import render, redirect
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from allauth.exceptions import ImmediateHttpResponse
from referral.views import track_lead
from user.models import CustomUser
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)



def index(request):
    # Render the HTML template index.html
    return render(request, "index.html")


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    # Render the HTML template index.html
    return Response("OK")



@api_view(["GET"])
@permission_classes([AllowAny])
def redirect_to_path(request, path):
    # redirect to a given url with /accounts/redirect stripped in the path
    protocol = "https://" if request.is_secure() else 'http://'
    url = protocol+request.get_host() + '/' + path
    return HttpResponse(f'''
 <html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>The Tudors</title>
    <meta http-equiv="refresh" content="0;URL=\'{url}\'" />
    <script>
    setTimeout(function(){{
        document.getElementById("msg").style.display="block"
    }}, 1000)
    </script>
  </head>
  <body style="background-color:white;background:radial-gradient(rgb(255, 168, 37), rgb(255, 136, 68));color:black">
    <p id="msg" style="display:none">Redirecting to <a href="{url}" style="color:black">{url}</a>.</p>
  </body>
</html>
                    ''')

class GoogleOAuth2AdapterIdToken(GoogleOAuth2Adapter):
    # Google has recommended to migrate to using ID tokens instead of access_token used in rest_auth
    def complete_login(self, request, app, token, **kwargs):
        idinfo = id_token.verify_oauth2_token(token.token, requests.Request(), app.client_id)
        if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            raise ValueError("Wrong issuer " + idinfo["iss"])
        extra_data = idinfo
        # id tokens store id in sub field
        extra_data["id"] = idinfo["sub"]
        login = self.get_provider().sociallogin_from_response(request, extra_data)
        return login


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2AdapterIdToken
    client_class = OAuth2Client
    callback_url = "https://prism.bloomscroll.com/accounts/google/login/callback/"


class AppleLogin(SocialLoginView):
    adapter_class = AppleOAuth2Adapter

class AccountAdapter(DefaultAccountAdapter):
    def new_user(self, request):
        """Save referral data to user object"""
        user = get_user_model()()
        user.set_invite_code()
        if request.session.get("HTTP_REFERER"):
            user.http_referer = request.session["HTTP_REFERER"]
        if request.session.get("CAMPAIGN"):
            user.campaign = request.session["CAMPAIGN"]
        if request.session.get("INVITE_CODE"):
            invite_code = request.session["INVITE_CODE"]
            user.referrer = get_user_model().objects.filter(invite_code=invite_code).first()
        return user

class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user successfully authenticates via a
        social provider, but before the login is actually processed
        (and before the pre_social_login signal is emitted).

        We're trying to solve different use cases:
        - social account already exists, just go on
        - social account has no email or email is unknown, just go on
        - social account's email exists, link social account to existing user
        """

        # Ignore existing social accounts, just do this stuff for new ones
        if sociallogin.is_existing:
            return

        # some social logins don't have an email address, e.g. facebook accounts
        # with mobile numbers only, but allauth takes care of this case so just
        # ignore it
        if "email" not in sociallogin.account.extra_data:
            return

        user = None
        # check if given email address already exists.
        # Note: __iexact is used to ignore cases
        try:
            email = sociallogin.account.extra_data["email"].lower()
            email_address = EmailAddress.objects.get(email__iexact=email)
            # if it does, connect this new social login to the existing user
            user = email_address.user

        # if it does not, let allauth take care of this new social account
        except EmailAddress.DoesNotExist:
            logger.debug(f'Email address {email} does not exist')
            try:
                user = CustomUser.objects.get(email__iexact=email)
            except:
                return
            if not user:
                return

        sociallogin.connect(request, user)
    def authentication_error(self, request, provider_id, error, exception, extra_context):
        # this seems to happen when logging in on chrome and have chrome auto switch to PWA
        raise ImmediateHttpResponse(redirect('/'))
        print(
            'SocialAccount authentication error!',
            'error',
            request,
            {'provider_id': provider_id, 'error': error.__str__(), 'exception': exception.__str__(), 'extra_context': extra_context},
        )

@api_view(["POST"])
@permission_classes([AllowAny])
def set_referer(request):
    # Capture referral info into session
    http_referer = request.data.get("http_referer")
    if http_referer:
        # only override referer if it's an external refer or no referer is set
        if not request.session.get("HTTP_REFERER") and ("bloomscroll" not in http_referer):
            request.session["HTTP_REFERER"] = http_referer
    # store the campaign id
    campaign = request.data.get("campaign")
    if campaign:
        request.session["CAMPAIGN"] = campaign
    # store the promo code
    promo_code = request.data.get("promo")
    if promo_code:
        request.session["PROMO_CODE"] = promo_code
    # store the referral destination
    dst = request.data.get("dst")
    if dst:
        request.session["REFERRAL_DESTINATION"] = dst
    # store the invite code
    invite_code = request.data.get("invite")
    if invite_code:
        request.session["INVITE_CODE"] = invite_code
        request.session["HTTP_REFERER"] = http_referer
        track_lead(request)
    return Response('ok')

def referal_middleware(get_response):
    # One-time configuration and initialization.
    def middleware(request):
        # Capture referral info into session
        if request.method == "GET":
            http_referer = request.META.get("HTTP_REFERER")
            if http_referer:
                # only override referer if it's an external refer or no referer is set
                if not request.session.get("HTTP_REFERER") and ("bloomscroll" not in http_referer):
                    request.session["HTTP_REFERER"] = http_referer

            # store the campaign id
            campaign = request.GET.get("c")
            if campaign:
                request.session["CAMPAIGN"] = campaign
            # store the promo code
            promo_code = request.GET.get("pc")
            if promo_code:
                request.session["PROMO_CODE"] = promo_code
            # store the invite code
            invite_code = request.GET.get("invite")
            if invite_code:
                request.session["INVITE_CODE"] = invite_code
                request.session["REFERRAL_DESTINATION"] = request.get_full_path()
                track_lead(request)

        response = get_response(request)
        # Code to be executed for each request/response after
        # the view is called.
        return response

    return middleware
