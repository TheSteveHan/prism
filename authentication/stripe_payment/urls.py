from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="billing-home"),
    path("current-subscription/", views.get_current_subscription),
    path("connected-accounts/", views.get_connected_accounts),
    path("connected-accounts/<account_id>", views.delete_connected_account),
    path("start-checkout/<str:tier>/", views.start_checkout, name="start-checkout"),
    path("create-payout-account/", views.create_payout_account, name="create-payout-account"),
    path("payout-dashboard/", views.payout_dashboard),
    path("config/", views.stripe_config),
    path("checkout/<str:price_id>/", views.create_checkout_session),
    path("success/<str:session_id>/", views.success),
    path("cancel/", views.cancel),
    path("webhook/", views.stripe_webhook),
    path("webhook/connect/", views.stripe_connect_webhook),
]
