from django.contrib import admin
from .models import Lead, Referral, Commission, Payout, PayoutSettings


class LeadAdmin(admin.ModelAdmin):
    list_display = ("affiliate", "source", "destination", "created_at")


class ReferralAdmin(admin.ModelAdmin):
    list_display = ("affiliate", "user", "status", "recurring_commission", "created_at", "updated_at")


class CommissionAdmin(admin.ModelAdmin):
    list_display = ("affiliate", "user", "status", "revenue", "commission", "created_at", "updated_at")


class PayoutAdmin(admin.ModelAdmin):
    list_display = ("affiliate", "email", "status", "amount", "created_at", "updated_at")


class PayoutSettingsAdmin(admin.ModelAdmin):
    list_display = ("affiliate", "email")


admin.site.register(Lead, LeadAdmin)
admin.site.register(Referral, ReferralAdmin)
admin.site.register(Commission, CommissionAdmin)
admin.site.register(Payout, PayoutAdmin)
admin.site.register(PayoutSettings, PayoutSettingsAdmin)
