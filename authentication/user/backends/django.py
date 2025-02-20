"""Django Authentication Backend for Authenticating against another Django backend"""
import re

import requests

from .base import BaseBackend

class DjangoBackend(BaseBackend):
    """Authenticate against another Django Service"""
    def __init__(self, host_url):
        self.host_url = host_url

    def get_username_from_credentials(self, request, username=None, password=None):
        """Sign in to anoher django server with the username and password to verify the username"""
        # get a new log in page/session
        login_page= requests.get(host_url)
        # extract the csrf token from log in page
        csrf_token = re.search("csrfmiddlewaretoken' value='([a-z,A-Z,0-9]*)", login_page.text)
        if csrf_token:
            csrf_token = csrf_token.group(1)
        # attempt to log in with token
        login_response = requests.post(
            LOGIN_URL,
            data={
                "email":username,
                "password":password,
                "csrfmiddlewaretoken": csrf_token
            }, cookies=dict(login_page.cookies),
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "referer":f"https://{self.host_url}",
            }
        )
        if login_response.ok:
            return username
        else:
            return None

