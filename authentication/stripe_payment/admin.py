from django.contrib import admin
from .models import StripeCustomer, StripeConnectAccount


class StripeCustomerAdmin(admin.ModelAdmin):
    list_display = ("user", "customer_id")

class StripeConnectAccountAdmin(admin.ModelAdmin):
    list_display = ("user_id", "account_id")

admin.site.register(StripeCustomer, StripeCustomerAdmin)
admin.site.register(StripeConnectAccount, StripeConnectAccountAdmin)
