"""User app views."""
import requests
import datetime
import os
import allauth
import mimetypes
from django.contrib import auth
from django.conf import settings
from django.http import HttpResponse
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from user.models import CampaignEmailRecord, CustomUser
from wsgiref.util import FileWrapper
from avatar.utils import (get_primary_avatar, get_default_avatar_url,
                          invalidate_cache)
from clients.analytics import log_event
from django.http import StreamingHttpResponse
from wsgiref.util import is_hop_by_hop
from django.conf import settings



@api_view(["GET"])
@authentication_classes((SessionAuthentication, JWTAuthentication))
@permission_classes((IsAuthenticated,))
def get_jwt_token(request):
    """Return a newly created JWT token for current user."""
    refresh = RefreshToken.for_user(request.user)
    return Response({"refresh": str(refresh), "access": str(refresh.access_token)})


def _get_profile_for_user(user):
    groups =  [g.name for g in user.groups.all()]
    res = {
        "username": user.username,
        "date_joined": user.date_joined,
        "user_id": user.uuid.hex,
        "email": user.email,
    }
    if groups:
        res['groups'] = groups
    if user.is_superuser:
        res['is_superuser'] = True
    if user.is_staff:
        res['is_staff'] = True
    return res

@api_view(["GET"])
@authentication_classes((JWTAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def get_profile(request):
    """Return the user object."""
    return Response(_get_profile_for_user(request.user))

@api_view(["GET"])
@permission_classes((AllowAny,))
def get_profile_by_id(request, user_id):
    """Return the user object."""
    user = CustomUser.objects.filter(uuid=user_id).first()
    if not user:
        return Response("User not found", 400)
    return Response(_get_profile_for_user(user))

@api_view(["post"])
@authentication_classes((JWTAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def deactivate(request):
    """Return the user object."""
    request.user.deactivated_at = datetime.datetime.now()
    request.user.save()
    return Response("ok",200)


@api_view(["POST"])
@permission_classes((AllowAny,))
def api_reset_password(request):
    """Send verification email"""
    email = request.data.get("email", "")
    form = allauth.account.forms.ResetPasswordForm({"email": email})
    if not form.is_valid():
        return Response({"detail": "Invalid email."}, status=400)
    else:
        form.save(request)
        return Response({"success": True}, status=200)

@api_view(["GET"])
@permission_classes((AllowAny,))
def search_users(request):
    """Return the user object."""
    user_ids = request.GET.get('user_ids', '')
    if user_ids:
        users = CustomUser.objects.filter(uuid__in=user_ids.split(',')).all()
    else:
        query = request.GET.get('query', '')
        users = CustomUser.objects.filter(email__icontains=query).all()
    return Response([ _get_profile_for_user(user) for user in users ])


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def search_user_by_username(request):
    """Search for user by useranme"""
    username = request.data.get("username")
    if not username:
        return Response([])
    res = CustomUser.objects.filter(username__istartswith=username).order_by('username').all()[:100]
    return Response([
        {'username':r.username}
        for r in res
    ])

@api_view(["POST"])
@authentication_classes((JWTAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated, AllowAny))
def web_logout(request):
    if request.user.is_authenticated:
        auth.logout(request)
    return Response('ok')

@api_view(["get"])
@permission_classes((IsAuthenticated,))
def get_profile_image_url(request):
    '''Get the url for profile image'''
    user = request.user
    avatar = get_primary_avatar(user, size=128)
    if avatar:
        # FIXME: later, add an option to render the resized avatar dynamically
        # instead of redirecting to an already created static file. This could
        # be useful in certain situations, particulary if there is a CDN and
        # we want to minimize the storage usage on our static server, letting
        # the CDN store those files instead
        url = avatar.avatar_url(size)
    else:
        social_accounts = request.user.socialaccount_set.all()
        if social_accounts:
            url = social_accounts[0].get_avatar_url()
        if not url:
            url = get_default_avatar_url()
    return Response(url)

def track_email_open(request, record_id, image_name):
    # this image name is user input, we have to be very careful
    # respond 404 for attempts to go back up any directory
    if ".." in image_name:
        return HttpResponse('', status=404)
    record = CampaignEmailRecord.objects.filter(record_id=record_id).first()
    if not record:
        return HttpResponse('', status=404)
    if not record.opened:
        record.opened = datetime.datetime.utcnow()
        record.open_headers = dict(request.headers)
        record.save()
    log_event(record.user_id, 'email_open', { 'c': record.campaign_id, 'h':dict(request.headers)})
    filename = os.path.join(settings.STATIC_ROOT, image_name)
    if not os.path.exists(filename):
        return HttpResponse('', status=404)
    with open(filename, 'rb') as f:
        mime_type, _ = mimetypes.guess_type(filename)
        wrapper = FileWrapper(f)
        response = HttpResponse(wrapper, content_type=mime_type)
        response['Content-Length'] = os.path.getsize(filename)
        return response
    return HttpResponse('', status=404)

def show_pw_reset_link(email):
    # back office only ...
    # log into the pod and get a reset email link
    from django.test.client import RequestFactory
    import os
    os.environ["LOG_EMAIL_CONTENT"]="1"
    rf = RequestFactory()
    req = rf.get('/password-reset')
    form = allauth.account.forms.ResetPasswordForm({"email": email})
    if not form.is_valid():
        return Response({"detail": "Invalid email."}, status=400)
    else:
        form.save(req)
        os.environ.pop("LOG_EMAIL_CONTENT", None)
        return Response({"success": True}, status=200)


class ProxyHttpResponse(StreamingHttpResponse):

    def __init__(self, url, headers=None, **kwargs):
        upstream = requests.get(url, stream=True, headers=headers)

        kwargs.setdefault('content_type', upstream.headers.get('content-type'))
        kwargs.setdefault('status', upstream.status_code)
        kwargs.setdefault('reason', upstream.reason)

        super().__init__(upstream.raw, **kwargs)

        for name, value in upstream.headers.items():
            if not is_hop_by_hop(name):
                self[name] = value

@api_view(["GET"])
@authentication_classes((SessionAuthentication, ))
@permission_classes((IsAuthenticated, ))
def admin_view_proxy(request, path):
    if not request.user.is_staff:
        return Response('Not Found', status=404)
    url = f'http://{settings.FE_SERVER}/{path}'
    response = requests.get(
        url, stream=True,
        headers={
            # intentionally hard coded in pain text here.
            # this is just an obfuscation
            'x-td-internal-admin-view-access-key':'aHardCodedAccessHey'
        }
    )
    if response.status_code != 200:
        return Response('Not found', status=404)
    return StreamingHttpResponse(
        response.raw,
        content_type=response.headers.get('content-type'),
        status=response.status_code,
        reason=response.reason)
