from django.contrib import admin
from .models import (
    User, VolunteerProfile, OrganizationProfile,
    Opportunity, Application, Notification, HourLog, Feedback
)

admin.site.register(User)
admin.site.register(VolunteerProfile)
admin.site.register(OrganizationProfile)
admin.site.register(Opportunity)
admin.site.register(Application)
admin.site.register(Notification)
admin.site.register(HourLog)
admin.site.register(Feedback)