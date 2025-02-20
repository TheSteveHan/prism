from rest_framework import serializers

from referral.models import Lead, Referral, Commission, Payout, PayoutSettings


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        exclude = ("affiliate", "id", "session_id")


class ReferralSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username")

    class Meta:
        model = Referral
        exclude = ("affiliate", "id", "user")


class CommissionSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username")

    class Meta:
        model = Commission
        exclude = ("affiliate", "id", "event_id", "user")


class PayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payout
        exclude = ("affiliate", "id")


class PayoutSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayoutSettings
        exclude = ("affiliate", "id")
