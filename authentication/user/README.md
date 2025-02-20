# Usage

```
include "user" in INSTALLED_APPS
add a "logo.png" in the static folder 
add "user.csrf.DisableCSRF" to disable CSRF
install the urls
    path("adminzzz/", admin.site.urls),
    path("accounts/", include(user_app)),
Optional: change and add "user.backends.DjangoBackend" to authentication backends
Modify custom sign up form:
change user/forms.py
```

## More configurations in settings.py
```
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = "/accounts/static/"

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_jwt.authentication.JSONWebTokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ),
}
JWT_AUTH = {"JWT_AUTH_HEADER_PREFIX": "JWT", "JWT_EXPIRATION_DELTA": datetime.timedelta(days=10)}
LOGIN_REDIRECT_URL = '../../'
LOGOUT_REDIRECT_URL = '../../'
PASSWORD_RESET_TIMEOUT_DAYS = 1
```
