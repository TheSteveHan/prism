import json
from django.test import SimpleTestCase, TransactionTestCase
from stripe_payment.views import handle_stripe_connect_event
from unittest.mock import patch
from stripe_payment.models import StripeConnectAccount
import stripe

class TestStripeConnectHandle(TransactionTestCase):
    @patch('stripe_payment.views._notify_payment_event', return_value=('ok', 200))
    def test_checkout_session_for_ticket_purchase(self, notify):
        with open('stripe_payment/tests/data/ticket_checkout.session.completed.json') as f:
            event = stripe.util.convert_to_stripe_object(json.load(f))
        body, status =  handle_stripe_connect_event(event)

    def test_account_update(self):
        StripeConnectAccount.objects.create(account_id="acc", account_type=1)
        with open('stripe_payment/tests/data/test_account.update.json') as f:
            event = stripe.util.convert_to_stripe_object(json.load(f))

        body, status =  handle_stripe_connect_event(event)
