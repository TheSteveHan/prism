from django.contrib import admin
from django.db.models import OuterRef, Subquery, Func, Value
from django.db.models.functions import Cast
from django.db.models import TextField
from .models import CustomUser, CampaignEmailRecord

class UserAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'username', 'date_joined', 'email', 'first_name', 'last_name', 'referrer', 'invite_code', 'http_referer', 'campaign', )
    search_fields = ('username', 'email', 'uuid')

class CampaignEmailRecordAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        user = CustomUser.objects.annotate(
            uuid_txt=Func(
                Cast('uuid', output_field=TextField()),
                Value('-'), Value(''),
                function='replace'
            )
        ).filter(uuid_txt=OuterRef('user_id'))
        new_qs = queryset.annotate(_email=Subquery(user.values('email')[:1]))
        return new_qs

    def email(self, obj):
        if hasattr(obj, '_email'):
            return obj._email
        return None

    list_display = ('record_id', 'user_id', 'campaign_id', 'timestamp', 'opened', 'email')
    search_fields = ('user_id', 'campaign_id')

admin.site.register(CustomUser, UserAdmin)
admin.site.register(CampaignEmailRecord, CampaignEmailRecordAdmin)
