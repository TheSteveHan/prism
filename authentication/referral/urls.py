from django.urls import path
from .views import get_leads, get_referrals, get_commissions, get_payouts, payout_settings_view, get_invite_code

urlpatterns = [
    path("leads/", get_leads, name="get_leads"),
    path("referrals/", get_referrals, name="get_referrals"),
    path("rewards/", get_commissions, name="get_commissions"),
    path("payouts/", get_payouts, name="get_payouts"),
    path("payout-settings/", payout_settings_view, name="payout_settings"),
    path("invite-code/", get_invite_code, name="get_invite_code"),
]
