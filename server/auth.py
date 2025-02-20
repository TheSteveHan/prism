import os
import requests
from .settings import app, db
from flask import request, make_response
from expiringdict import ExpiringDict
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
TOKEN_CACHE = ExpiringDict(max_len=10000, max_age_seconds=300)

AUTH_SERVER = os.environ.get('AUTH_SERVER', 'localhost:8000')

class AuthenticationError(Exception):
    def __init__(self, headers, body, status):
        super()
        self.headers = headers
        self.body = body
        self.status = status

def _get_user_profile_from_auth():
    res = {}
    token = request.headers.get('Authorization')
    if not token:
        if not request.cookies.get("sessionid", None):
            raise AuthenticationError({}, "Permission Denied", 403)
        if token in TOKEN_CACHE:
            return TOKEN_CACHE[token]
        resp = requests.get(f"http://{AUTH_SERVER}/api/user/profile/", cookies=request.cookies)
    else:
        cached_user = TOKEN_CACHE.get(token, None)
        if cached_user:
            return cached_user
        headers ={
            'Authorization': f"{token}"
        }
        resp = requests.get(f"http://{AUTH_SERVER}/api/user/profile/", headers=headers)
    if not resp.ok:
        resp.close()
        raise AuthenticationError(resp.headers, resp.text, resp.status_code)
    res = resp.json()
    resp.close()
    if token:
        TOKEN_CACHE[token] = res
    return res


def _get_user_from_request(create_if_new=True):
    res = _get_user_profile_from_auth()
    if not res:
        return None
    res["user_id"] = str(res['user_id'])
    res["id"] = None
    return res

def get_user_from_request(return_none=False, create_if_new=True):
    try:
        return _get_user_from_request(create_if_new)
    except AuthenticationError as e:
        if not return_none:
            raise e
        return None

def _get_checkout_url(params):
    res = requests.post(
        f'http://{AUTH_SERVER}/internal/api/billing/stripe/start-checkout-for-product',
        json=params
    )
    if not res.ok:
        logger.exception(f"Failed to checkout. {res.status_code} {res.content}")
        return None
    return res.json()['url']

def get_checkout_url(params):
    # call the local verison here so we can mock it in test
    return _get_checkout_url(params)

@app.errorhandler(AuthenticationError)
def handle_auth_error(e):
    response = make_response(e.body, e.status)
    response.headers["Content-Type"] = "application/json"
    return response
