from django.urls import path
from .views import get_jwt_token, get_profile, search_user_by_username, get_profile_image_url, web_logout, deactivate
from .saml_views import index, attrs, metadata

urlpatterns = [
    # JWT token auth
    path("jwt-token/", get_jwt_token, name="get_jwt_token"),
    path("profile/", get_profile, name="get_profile"),
    path("deactivate/", deactivate, name="deactivate"),
    path("profile-image/", get_profile_image_url, name="get_profile_image_url"),
    path("search/", search_user_by_username, name="search_user"),
    path("web-logout/", web_logout, name="web_logout"),
    path("saml/", index, name="index"),
    path("saml/attrs", attrs, name="attrs"),
    path("saml/metadata", metadata, name="metadata"),
]
