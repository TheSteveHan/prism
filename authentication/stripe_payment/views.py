import requests
import datetime
import os
import stripe
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from authentication.waffles import BS_BASIC, BS_PREMIUM
from .models import StripeCustomer, LicensePurchase, StripeConnectAccount, StripeConnectAccountType
from referral.views import track_charge
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

PRICE_FREE = "FREE_PLAN"
TIER_FREE = "FREE"
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_ENDPOINT_SECRET = os.environ.get("STRIPE_ENDPOINT_SECRET")
STRIPE_ENDPOINT_SECRET_CONNECT = os.environ.get("STRIPE_ENDPOINT_SECRET_CONNECT")
STRIPE_CALLBACK_DOMAIN= os.environ.get("STRIPE_CALLBACK_DOMAIN", "bloomscroll.com")
stripe.api_key = STRIPE_SECRET_KEY

subscriptions = [
    {"name": "Free",
     "price": 0,
     "price_desc": "Free plan",
     "desc": "Some description...",
     "tier_id": TIER_FREE,
     "price_id": PRICE_FREE,
     "is_free": True},
    {
        "name": "Monthly",
        "price": 8,
        "price_desc": "$8/Month",
        "desc": "Just the basics",
        "price_id": "price_XXXXXXXXXXXXXXXXXX" if settings.DEBUG else "price_XXXXXXXXXXX",
        "tier_id": "MONTHLY",
        "group": BS_BASIC,
    },
    {
        "name": "Annual",
        "price": 48,
        "price_desc": "$48/Year",
        "desc": "All access",
        "price_id": "price_YYYYYYYYYYYYY" if settings.DEBUG else "price_YYYYYYYYYY",
        "tier_id": "ANNUAL",
        "group": BS_PREMIUM,
    },
]

price_id_to_subscription = {
    sub['price_id']:sub
    for sub in subscriptions
}

tier_to_price_id={
    sub['tier_id']:sub["price_id"]
    for sub in subscriptions
    if sub.get('tier_id')
}

oneoffs = [ ]

price_id_to_group = {x["price_id"]: x["group"] for x in subscriptions if x.get("group")}

def get_domain_url(request):
    if STRIPE_CALLBACK_DOMAIN.startswith("http"):
        return STRIPE_CALLBACK_DOMAIN
    return "https://"+STRIPE_CALLBACK_DOMAIN

@login_required
def home(request):
    stripe_customer = StripeCustomer.objects.filter(user=request.user).first()
    if stripe_customer and stripe_customer.subscription_id:
        subscription = stripe.Subscription.retrieve(stripe_customer.subscription_id)
        if subscription.status == "active":
            # TODO this is only always fetching the first product
            product = stripe.Product.retrieve(subscription["items"]["data"][0].plan.product)
            price_id = subscription["items"]["data"][0].price.id
            return render(
                request,
                "stripe_payment/home.html",
                {
                    "subscription": subscription,
                    "product": product,
                    "subscriptions": [x for x in subscriptions if x.get("price_id") != price_id],
                    "oneoffs": oneoffs,
                },
            )
        else:
            # clean up if the subscription is canceled manually
            stripe_customer.subscription_id = None
            stripe_customer.save()
    return render(request, "stripe_payment/home.html", {"subscriptions": subscriptions, "oneoffs": oneoffs})

@login_required
def start_checkout(request, tier):
    price_id = tier_to_price_id.get(tier)
    if not price_id:
        return HttpResponse('Invalid Tier', status=400)
    return render(
        request,
        "stripe_payment/start_checkout.html",
        {"price_id":price_id}
    )

@api_view(["POST"])
@permission_classes([AllowAny])
def start_checkout_for_product(request):
    seller_params = request.data.get('seller_params')
    stripe_params = request.data.get('stripe_params')
    sc_account = StripeConnectAccount.objects.filter(**seller_params).first()
    if not sc_account:
        return JsonResponse({'error':"NO_CONNECT_ACC"}, status=404)
    session = stripe.checkout.Session.create(
        **stripe_params,
        stripe_account=sc_account.account_id,
    )
    return JsonResponse({'url': session.url})

@login_required
def payout_dashboard(request):
    sc_account = StripeConnectAccount.objects.filter(user_id=request.user.uuid.hex).first()
    if not sc_account:
        return HttpResponse("No account found", status=400)
    if sc_account.account_type == StripeConnectAccountType.EXPRESS:
        link = stripe.Account.create_login_link(sc_account.account_id)
        if link.get('url'):
            return redirect(link.get('url'))
    else:
        return redirect('https://dashboard.stripe.com')
    return HttpResponse('Failed get link for account', status=500)

@login_required
def create_payout_account(request):
    next_url = request.GET.get('next')
    sc_account = StripeConnectAccount.objects.filter(user_id=request.user.uuid.hex).first()
    if not sc_account:
        account = stripe.Account.create(
            type="standard",
            email=request.user.email,
            metadata={
                'user_id': request.user.uuid.hex,
                'email': request.user.email
            }
        )
        sc_account, created = StripeConnectAccount.objects.get_or_create(
            user_id=request.user.uuid.hex,
            account_type=1,
            defaults={
                "account_id": account.id,
            },
        )
    if not sc_account:
        return HttpResponse('Failed to create account', status=500)
    domain_url = get_domain_url(request)
    refresh_url = domain_url + "/api/billing/stripe/create-payout-account"
    if next_url:
        refresh_url+=f'?next={next_url}'
    account_link = stripe.AccountLink.create(
        account=sc_account.account_id,
        refresh_url=refresh_url,
        return_url=(domain_url + "/") if not next_url else next_url,
        type="account_onboarding",
    )
    if account_link.get('url'):
        return redirect(account_link.get('url'))
    return HttpResponse('Failed get link for account', status=500)

@csrf_exempt
def stripe_config(request):
    if request.method == "GET":
        stripe_config = {"publicKey": STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config, safe=False)


def _create_checkout_response(stripe_customer, params, request):
    if stripe_customer:
        params["customer"] = stripe_customer.customer_id
    else:
        params["customer_email"] = request.user.email
    try:
        checkout_session = stripe.checkout.Session.create(**params)
        return JsonResponse({"sessionId": checkout_session["id"]})
    except stripe.error.InvalidRequestError as e:
        if e.param == "customer" and e.code == "resource_missing":
            # the stripe customer is deleted manually on stripe
            stripe_customer.delete()
            del params["customer"]
            params["customer_email"] = request.user.email
            checkout_session = stripe.checkout.Session.create(**params)
            return JsonResponse({"sessionId": checkout_session["id"]})
        logger.exception(e)
        raise
    except Exception as e:
        logger.exception(e)
        raise


@csrf_exempt
def create_purchase_session(request, price_id, report_id):
    if request.method != "POST":
        return
    stripe_customer = StripeCustomer.objects.filter(
        user=request.user,
    ).first()
    # else start a new purchase
    domain_url = ("https://" if request.is_secure() else "http://") + request.META["HTTP_HOST"]
    params = {
        "client_reference_id": request.user.uuid.hex if request.user.is_authenticated else None,
        "success_url": domain_url + "/api/billing/stripe/success/{CHECKOUT_SESSION_ID}/",
        "cancel_url": domain_url + "/reports",
        "payment_method_types": ["card"],
        "mode": "payment",
        "metadata": {"report_id": report_id},
        "allow_promotion_codes": True,
        "line_items": [
            {
                "price": price_id,
                "quantity": 1,
            }
        ],
    }
    return _create_checkout_response(stripe_customer, params, request)


@csrf_exempt
def create_checkout_session(request, price_id):
    if request.method != "GET":
        return
    stripe_customer = StripeCustomer.objects.filter(
        user=request.user,
    ).first()
    # modify the subscription if there's already one
    if stripe_customer and stripe_customer.subscription_id:
        subscription = stripe.Subscription.retrieve(stripe_customer.subscription_id)
        if subscription.status != "active":
            # delete record of outdated subscription
            stripe_customer.subscription_id = None
            stripe_customer.save()
        else:
            if price_id == PRICE_FREE:
                # delete subscription and waffles
                stripe.Subscription.delete(stripe_customer.subscription_id, prorate=True)
                subscription_groups = Group.objects.filter(name__in=price_id_to_group.values()).all()
                for group in subscription_groups:
                    group.user_set.remove(request.user)
                return JsonResponse({"status": "ok", "refresh": True})

            # upgrade old plan to new
            old_price_id = subscription["items"]["data"][0].price.id
            if old_price_id == price_id:
                # nothing to do
                return JsonResponse({"status": "ok", "refresh": True})
            # set old price's quantity to 0 and new to 1
            session = stripe.Subscription.modify(
                stripe_customer.subscription_id,
                items=[
                    {
                        "id": subscription["items"]["data"][0].id,
                        "deleted": True,
                    },
                    {"price": price_id, "quantity": 1},
                ],
            )
            handle_subscription_session(session, stripe_customer=stripe_customer)
            return JsonResponse({"status": "ok", "refresh": True})
    # else start a new subscription
    domain_url = get_domain_url(request)
    params = {
        "client_reference_id": request.user.uuid.hex if request.user.is_authenticated else None,
        "success_url": domain_url + "/api/billing/stripe/success/{CHECKOUT_SESSION_ID}/",
        "cancel_url": domain_url + "/api/billing/stripe/cancel/",
        "payment_method_types": ["card"],
        "allow_promotion_codes": True,
        "mode": "subscription",
        "metadata": {"group": price_id_to_group.get(price_id)},
        "line_items": [
            {
                "price": price_id,
                "quantity": 1,
            }
        ],
    }
    return _create_checkout_response(stripe_customer, params, request)


@login_required
def success(request, session_id):
    session = stripe.checkout.Session.retrieve(session_id)
    if not session:
        return
    if session.mode == "subscription":
        handle_subscription_session(session)
        #return render(request, "stripe_payment/success.html")
        return redirect("/payment-welcome")
    elif session.mode == "payment":
        success, error = handle_purchase_session(session)
        if not success:
            return render(request, "stripe_payment/error.html", context={"error": error})
        return redirect("/payment-welcome")
    return redirect("/payment-welcome")


@login_required
def cancel(request):
    return redirect("/payment-cancel")


def handle_purchase_session(session, stripe_customer=None):
    # update stripe customer
    if session.metadata.report_id:
        error, success = unlock_report(session.metadata.report_id)
        if not success:
            return False, error
    else:
        return False, "Checkout failed. Please contact us at contact@{STRIPE_CALLBACK_DOMAIN}."
    stripe_customer_id = session.get("customer")
    client_reference_id = session.get("client_reference_id")
    user = get_user_model().objects.filter(uuid=client_reference_id).first()
    if not user:
        return True, "Success"
    if not stripe_customer:
        # Get the user and create a new StripeCustomer
        stripe_customer, created = StripeCustomer.objects.get_or_create(
            user=user,
            defaults={
                "customer_id": stripe_customer_id,
            },
        )
    # Add a liense purchase
    purchase = LicensePurchase(
        user=user,
        customer_id=stripe_customer_id,
        payment_id=session.get("payment_intent"),
        expiration_time=datetime.datetime.utcnow() + datetime.timedelta(days=365),
    )
    purchase.save()
    return True, "Success"


def handle_subscription_session(session, stripe_customer=None):
    # Fetch all the required data from session
    stripe_customer_id = session.get("customer")
    stripe_subscription_id = session.get("subscription") or session["items"]["data"][0].subscription
    if not stripe_customer:
        client_reference_id = session.get("client_reference_id")
        # Get the user and create a new StripeCustomer
        user = get_user_model().objects.filter(uuid=client_reference_id).first()
        if not user:
            return False, "Invalid client_reference_id"
        stripe_customer, created = StripeCustomer.objects.get_or_create(
            user=user,
            defaults={
                "customer_id": stripe_customer_id,
                "subscription_id": stripe_subscription_id,
            },
        )
    else:
        user = stripe_customer.user
        created = False
    if not created:
        if stripe_customer.subscription_id != stripe_subscription_id:
            if stripe_customer.subscription_id and stripe_subscription_id:
                # if an old subscription is already there, cancel it
                # This is a race condition that would only be triggered
                # when a user subscribed and then subscribed again from the same page
                # this is not involved when properly upgrading an subscription
                try:
                    stripe.Subscription.delete(stripe_customer.subscription_id, prorate=True)
                except Exception as e:
                    # TODO do we need to do anything here if we can't delete the old subscription?
                    logger.exception(e)
            stripe_customer.subscription_id = stripe_subscription_id
            # TODO if this fails we would need to manually sync this subscription again
            stripe_customer.save()
    # update waffles
    group_name = session.get("metadata", {}).get("group") or price_id_to_group.get(session["items"]["data"][0].price.id)
    print(f"{user.username} just subscribed to {group_name}")
    if not group_name:
        return False, "Missing 'group' in metadata and missing price_id_to_group mapping"
    subscription_groups = Group.objects.filter(name__in=price_id_to_group.values()).all()
    for group in subscription_groups:
        if group.name != group_name:
            group.user_set.remove(user)
        else:
            group.user_set.add(user)
    return True, "success"

def _notify_payment_event(event):
    res = requests.post(
        f'http://{settings.API_SERVER}/internal/handle-payment-events',
        json=event
    )
    return res.text, res.status_code

def set_payout_enabled(user_id, enabled):
    try:
        res = requests.post(
            f'http://{settings.API_SERVER}/internal/set-payout-enabled',
            json={
                'user_id': user_id,
                'enabled': enabled
            }
        )
        if res.ok:
            return None
        return f"Failed to update: {res.status_code}"
    except Exception as e:
        return f"Failed to update: {e}"



def sync_all_accounts():
    accounts = StripeConnectAccount.objects.all()
    print(f"Found {len(accounts)} accounts")
    for acc in accounts:
        acc_id = acc.account_id
        print(f"syncing {acc_id}")
        if not acc.info:
            try:
                acc.info = stripe.Account.retrieve(acc_id)
            except Exception as e:
                print(f"Failed to fetch account {e}")
                continue
            acc.save()
        res = update_account_data(acc.info)
        if res:
            print(f"Error: {res}")
        else:
            print("Success")

def update_account_data(account_data):
    if not account_data:
        return "Account data not found"
    account_id = account_data.get('id')
    if not account_id:
        return "Account id not found"
    account = StripeConnectAccount.objects.filter(account_id=account_id).first()
    if not account:
        return None
    enabled = account_data.get("charges_enabled")
    if enabled is None:
        return "Missing field charges_enabled"
    return set_payout_enabled(account.user_id, enabled)

def handle_stripe_connect_event(event):
    account_id = event.account
    if event["type"] == "account.updated":
        account = event['data']['object']
        error = update_account_data(account)
        if error:
            return error, 400
        else:
            return 'ok', 200
    if event["type"] == "checkout.session.completed":
        if False:
            # dump event for test
            with open("stripe_payment/tests/data/????", "w") as f:
                json.dump(stripe.util.convert_to_dict(event), f)
        session = event['data']['object']
        client_reference_id = session.get("client_reference_id")
        maybe_fix_payment_intent_description(session=session, account_id=account_id)
        if client_reference_id and client_reference_id.startswith('v2.'):
            evt = {
                'type': 'checkout.session.completed',
                'client_reference_id': client_reference_id,
            }
            try:
                evt['amount_total']= event.data.object.amount_total
                evt['currency']= event.data.object.currency
                evt['timestamp']= event.data.object.created
                evt['receipt_email']= event.data.object.customer_details.email
                evt['receipt_name']= event.data.object.customer_details.name
            except Exception:
                pass
            return _notify_payment_event(evt)
    return 'skipped', 200

@csrf_exempt
def stripe_connect_webhook(request):
    stripe.api_key = STRIPE_SECRET_KEY
    endpoint_secret = STRIPE_ENDPOINT_SECRET_CONNECT
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
    event = None
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        # Invalid payload
        logger.error(f"Invalid Payload")
        return JsonResponse({"error":"Invalid Payload"}, status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        logger.error(f"Invalid Signature")
        return JsonResponse({"error":"Invalid Signature"}, status=400)
    if not settings.DEBUG and not event['livemode']:
        return HttpResponse(status=200)
    body, status = handle_stripe_connect_event(event)
    if status != 200:
        logger.error(f"body")
    return HttpResponse(body, status=status)

@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = STRIPE_SECRET_KEY
    endpoint_secret = STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
    event = None

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        # Invalid payload
        logger.error(f"Invalid Payload")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        logger.error(f"Invalid Signature")
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        if session.mode == "subscription":
            success, error = handle_subscription_session(session)
        elif session.mode == "payment":
            success, error = handle_purchase_session(session)
        if not success:
            logger.error(f"Failed to process")
            return HttpResponse(error, 400)
    elif event["type"] == "charge.succeeded" or event["type"] == "charge.refunded":
        event_id = event["id"]
        customer_id = event["data"]["object"]["customer"]
        if not customer_id:
            logger.error(f"Rejected: {event_id}. customer_id missing")
            return HttpResponse("Customer not found", status=400)
        stripe_customer = StripeCustomer.objects.filter(
            customer_id=customer_id,
        ).first()
        if stripe_customer:
            track_charge(
                stripe_customer.user,
                event["data"]["object"]["amount_captured"] / 100.0
                if event["type"] == "charge.succeeded"
                else -event["data"]["object"]["amount_refunded"] / 100.0,
                event_id,
            )
        else:
            logger.error(f"Rejected: {event_id}. StripeCustomer({customer_id}) not found")
            return HttpResponse(f"Rejected: {event_id}. StripeCustomer({customer_id}) not found", status=400)
    return HttpResponse(status=200)


def maybe_fix_payment_intent_description(session_id=None, account_id=None, session=None):
    try:
        if not session.payment_intent:
            return False
        if not session or 'line_items' not in session:
            session = stripe.checkout.Session.retrieve(
                session_id or session.id,
                stripe_account=account_id,
                expand=['line_items', 'customer', 'payment_intent']
            )
        try:
            customer_email = session.customer_details.email
            customer_name = session.customer_details.name
        except:
            customer_email = ''
            customer_name = ''
        description = []
        for line_item in session.line_items.data:
            product_id = line_item.price.product
            product_desc = stripe.Product.retrieve(product_id, stripe_account=account_id).description
            desc = str(line_item.quantity)+" x "+ line_item.description
            if product_desc:
                desc += f" - {product_desc}"
            description.append(desc)
        description = ", ".join(description)
        session.payment_intent.description = description
        session.payment_intent.metadata = {
            "Customer Email":customer_email,
            "Customer Name": customer_name,
            "Description": description,
        }
        res = session.payment_intent.save()
        logger.info(f'updated payment intent {session.payment_intent.id}')
        return True
    except Exception as e:
        logger.exception(e)
        return False

@api_view(["GET"])
@permission_classes((IsAuthenticated,))
def get_current_subscription(request):
    stripe_customer = StripeCustomer.objects.filter(
        user=request.user
    ).first()
    current_tier = price_id_to_subscription[PRICE_FREE]
    if stripe_customer and stripe_customer.subscription_id:
        subscription = stripe.Subscription.retrieve(stripe_customer.subscription_id)
        if subscription.status != "active":
            # delete record of outdated subscription
            stripe_customer.subscription_id = None
            stripe_customer.save()
        else:
            price_id = subscription["items"]["data"][0].price.id
            current_tier = price_id_to_subscription.get(price_id, current_tier)
    print(current_tier)
    res = {
        "name": current_tier['name'],
        "price_desc": current_tier['price_desc'],
        "tier_id": current_tier['tier_id']
    }
    return Response(res, status=200)

@api_view(["GET"])
@permission_classes((IsAuthenticated,))
def get_connected_accounts(request):
    uid = request.user.uuid.hex
    accounts = StripeConnectAccount.objects.filter(user_id=uid).all()
    res = []
    for acc in accounts:
        data = {
            'account_id': acc.account_id,
            'account_type': acc.account_type,
        }
        if acc.info:
            data['email'] = acc.info.get('email')
            data['payouts_enabled'] = acc.info.get('payouts_enabled')
        res.append(data)
    return Response(res, status=200)

@api_view(["DELETE"])
@permission_classes((IsAuthenticated,))
def delete_connected_account(request, account_id):
    uid = request.user.uuid.hex
    StripeConnectAccount.objects.filter(user_id=uid, account_id=account_id).delete()
    return Response('ok', status=200)
