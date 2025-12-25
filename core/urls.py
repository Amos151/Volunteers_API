from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    RegisterVolunteerView, RegisterOrgView,
    MyVolunteerProfileView, MyOrgProfileView,
    OpportunityCreateListView, OpportunityRetrieveUpdateDeleteView,
    OpportunitySearchView, ApplyToOpportunityView,
    MyApplicationsView, OpportunityApplicantsView, UpdateApplicationStatusView,
    MyNotificationsView, MarkNotificationReadView,
    LogHoursView, MyHoursView,
    LeaveFeedbackView
)

urlpatterns = [
    # Authorization 
    path("auth/register/volunteer/", RegisterVolunteerView.as_view()),
    path("auth/register/org/", RegisterOrgView.as_view()),
    path("auth/token/", TokenObtainPairView.as_view()),
    path("auth/token/refresh/", TokenRefreshView.as_view()),

    # Profiles
    path("me/volunteer-profile/", MyVolunteerProfileView.as_view()),
    path("me/org-profile/", MyOrgProfileView.as_view()),

    # Opportunities
    path("opportunities/", OpportunityCreateListView.as_view()),  
    path("opportunities/<int:pk>/", OpportunityRetrieveUpdateDeleteView.as_view()),
    path("opportunities/search/", OpportunitySearchView.as_view()),

    # Apply + status
    path("opportunities/<int:opportunity_id>/apply/", ApplyToOpportunityView.as_view()),
    path("me/applications/", MyApplicationsView.as_view()),
    path("opportunities/<int:opportunity_id>/applicants/", OpportunityApplicantsView.as_view()),
    path("applications/<int:pk>/status/", UpdateApplicationStatusView.as_view()),

    # Notifications
    path("me/notifications/", MyNotificationsView.as_view()),
    path("notifications/<int:pk>/read/", MarkNotificationReadView.as_view()),

    # Tracking
    path("hours/log/", LogHoursView.as_view()),
    path("me/hours/", MyHoursView.as_view()),

    # Feedback
    path("feedback/", LeaveFeedbackView.as_view()),
]

