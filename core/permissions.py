from rest_framework.permissions import BasePermission
from .models import User, Opportunity, Application, HourLog, Feedback

class IsVolunteer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Role.VOLUNTEER)

class IsOrganization(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Role.ORG)

class IsOrgOwnerOfOpportunity(BasePermission):
    def has_object_permission(self, request, view, obj: Opportunity):
        return hasattr(request.user, "org_profile") and obj.organization.user_id == request.user.id

class IsVolunteerOwnerOfApplication(BasePermission):
    def has_object_permission(self, request, view, obj: Application):
        return hasattr(request.user, "volunteer_profile") and obj.volunteer.user_id == request.user.id

class IsOrgOwnerViaApplication(BasePermission):
    def has_object_permission(self, request, view, obj: Application):
        return hasattr(request.user, "org_profile") and obj.opportunity.organization.user_id == request.user.id
