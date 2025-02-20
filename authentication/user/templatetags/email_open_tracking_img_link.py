from django import template
from user.models import CampaignEmailRecord
register = template.Library()

@register.simple_tag
def email_open_tracking_img_link(user, campaign_id, img_name):
    # create a link that tracks if a user opened a specific email
    new_record = CampaignEmailRecord(user_id=user.uuid.hex, campaign_id=campaign_id)
    new_record.set_record_id()
    # just in case we've previously created this
    new_record, created = CampaignEmailRecord.objects.get_or_create(
        user_id=new_record.user_id,
        campaign_id=new_record.campaign_id,
        defaults={'record_id': new_record.record_id},
    )
    record_id = new_record.record_id
    return f'https://bloomscroll.com/static-images/{record_id}/{img_name}'
