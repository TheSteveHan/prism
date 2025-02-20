BS_BASIC = "bc_basic"
BS_PREMIUM = "bc_premium"


# create the groups for basic and premium features
def config_waffles():
    from waffle.models import Flag
    from django.contrib.auth.models import Group

    # get or create the product groups
    basic_group, _ = Group.objects.get_or_create(name=BS_BASIC)
    premium_group, _ = Group.objects.get_or_create(name=BS_PREMIUM)
    # new flags here will be crfeated in prod,
    ######################################################################
    # WARNING:existing flags would NOT be updated by changing it here!!! #
    ######################################################################
    all_flags = {
        BS_BASIC: {
            "superusers": True,
            "staff": True,
        },
        BS_PREMIUM: {
            "superusers": True,
            "staff": True,
        },
    }
    # flag assignment to groups
    ######################################################################
    # WARNING:existing flags would NOT be updated by changing it here!!! #
    ######################################################################
    basic_flags = {BS_BASIC}
    premium_flags = {BS_PREMIUM}

    for flag_name, flag_params in all_flags.items():
        flag, created = Flag.objects.get_or_create(name=flag_name, defaults=flag_params)

        # assign the flag to groups
        # note: re-adding a group to a flag that already has it won't add it again
        if flag_name in basic_flags:
            flag.groups.add(basic_group)
        if flag_name in premium_flags:
            flag.groups.add(premium_group)

