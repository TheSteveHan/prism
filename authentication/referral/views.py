from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django_pg_bulk_update import bulk_update_or_create
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from referral.models import Lead, Referral, Commission, Payout, PayoutSettings, REFERRAL_STATUS_FREE
from referral.serializers import (
    LeadSerializer,
    ReferralSerializer,
    CommissionSerializer,
    PayoutSerializer,
    PayoutSettingsSerializer,
)

@api_view(["GET"])
def get_referral_metrics(request):
    lead_count = Lead.objects.filter(affiliate=request.user).count()
    referral_count = Referral.objects.filter(affiliate=request.user).count()
    # TODO figure out how to query unique users here
    sustainer_count = Commission.objects.filter(affiliate=request.user).count()
    return Response({
        'leads': lead_count,
        'referrals': referral_count,
        'sustainers': sustainer_count
    })

@api_view(["GET"])
@authentication_classes((JWTAuthentication,))
@permission_classes((IsAuthenticated,))
def get_payouts(request):
    all_payouts = Payout.objects.filter(affiliate=request.user).order_by("-created_at").all()
    return Response(PayoutSerializer(all_payouts, many=True).data)


@api_view(["GET"])
@authentication_classes((JWTAuthentication,))
@permission_classes((IsAuthenticated,))
def get_leads(request):
    all_leads = Lead.objects.filter(affiliate=request.user).order_by("-created_at").all()
    return Response(LeadSerializer(all_leads, many=True).data)


@api_view(["GET"])
@authentication_classes((JWTAuthentication,))
@permission_classes((IsAuthenticated,))
def get_referrals(request):
    all_referrals = Referral.objects.filter(affiliate=request.user).order_by("-created_at").all()
    return Response(ReferralSerializer(all_referrals, many=True).data)


@api_view(["GET"])
@authentication_classes((JWTAuthentication,))
@permission_classes((IsAuthenticated,))
def get_commissions(request):
    all_commissions = Commission.objects.filter(affiliate=request.user).order_by("-created_at").all()
    return Response(CommissionSerializer(all_commissions, many=True).data)


@api_view
@authentication_classes((JWTAuthentication,))
@permission_classes((IsAuthenticated,))
def payout_settings_view(request):
    if request.method == "GET":
        settings = PayoutSettings.objects.filter(affiliate=request.user).first()
        return Response(PayoutSettingsSerializer(settings).data)
    else:
        serializer = PayoutSettingsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
        return Response(serializer.data)


@api_view(["GET"])
@authentication_classes((JWTAuthentication,))
@permission_classes((IsAuthenticated,))
def get_invite_code(request):
    return Response(request.user.invite_code)


def track_lead(request):
    # Keep track of the clicks on referral links as Leads
    if not request.session.session_key:
        request.session.save()
    if request.session.session_key and request.session.get("INVITE_CODE"):
        invite_code = request.session.get("INVITE_CODE")
        affiliate = get_user_model().objects.filter(invite_code=invite_code).first()
        if not affiliate:
            return
        session_id = request.session.session_key
        source = request.session.get("HTTP_REFERER")
        destination = request.session.get("REFERRAL_DESTINATION", request.get_full_path())
        bulk_update_or_create(
            Lead,
            {
                session_id: {
                    "affiliate": affiliate,
                    "source": source,
                    "destination": destination,
                }
            },
            key_fields=["session_id"],
            update=True,
        )


@receiver(user_signed_up)
def on_user_signed_up(request, user, **kwargs):
    affiliate = user.referrer
    if not affiliate:
        return
    new_referral = Referral(
        user=user,
        affiliate=affiliate,
        status=REFERRAL_STATUS_FREE,
        init_commission=0.3,
        recurring_commission=0.3,
    )
    new_referral.save()


def track_charge(user, value, event_id):
    # update referral state
    # create new commission
    # charged value can be 0 when refunded
    affiliate = user.referrer
    if not affiliate:
        return
    referral = Referral.objects.filter(affiliate=affiliate, user=user).first()
    if not referral:
        return
    bulk_update_or_create(
        Commission,
        {
            event_id: {
                "user": user,
                "affiliate": affiliate,
                "status": "pending" if value > 0 else "refunded",
                "revenue": value,
                # TODO this causes issue when upgrading commission level,
                # should attempt to undo commission instead
                "commission": value * referral.recurring_commission,
                "event_id": event_id,
            }
        },
        key_fields=["event_id"],
        update=True,
    )
    return
