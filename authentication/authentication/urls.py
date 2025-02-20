from django.contrib import admin
from django.urls import path,re_path, include
from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from .views import GoogleLogin, AppleLogin, health, redirect_to_path, set_referer
from user.views import api_reset_password, track_email_open, get_profile_by_id, admin_view_proxy, search_users
from referral.views import get_referral_metrics
from stripe_payment.views import create_payout_account, start_checkout_for_product


urlpatterns = [
    # Django admin site
    path("adminzzz/", admin.site.urls),
    # use django all auth for api reset
    path(r"api/user/password/reset/", api_reset_password, name="api_password_reset"),
    # API views for rest-auth endppoints
    path("api/user/", include("dj_rest_auth.urls")),
    path("api/user/registration/", include("dj_rest_auth.registration.urls")),
    path("api/user/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/user/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/user/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("api/user/", include("user.urls")),
    path("api/user/auth/google", GoogleLogin.as_view(), name="google_login"),
    path("api/user/auth/apple", AppleLogin.as_view(), name="apple_login"),
    path("api/user/referral/", set_referer, name="set_referer"),
    # Application views for server-side rendered pages
    # Allauth
    path("accounts/", include("allauth.urls")),
    path("api/billing/stripe/", include("stripe_payment.urls")),
    path("health", health, name="health"),
    re_path("redirect/(?P<path>.*)", redirect_to_path, name="redirect"),
    path("api/referral/", include('referral.urls')),
    # email open tracking
    path("static-images/<record_id>/<image_name>", track_email_open),
    path("internal/api/user/referral/metrics", get_referral_metrics),
    path("internal/api/billing/stripe/create-payout-account", create_payout_account),
    path("internal/api/billing/stripe/start-checkout-for-product", start_checkout_for_product),
    path("internal/api/user/profile/by-id/<user_id>", get_profile_by_id),
    path("internal/api/user/profile/search", search_users),
    path("internal/api/user/admin-view-proxy/<path:path>",  admin_view_proxy),
]

