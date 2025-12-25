from django.db.models import Q
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from .models import User, VolunteerProfile, OrganizationProfile, Opportunity, Application, Notification, HourLog, Feedback
from .serializers import (
    RegisterVolunteerSerializer, RegisterOrgSerializer,UserSerializer,
    VolunteerProfileSerializer, OrganizationProfileSerializer,
    OpportunitySerializer, ApplicationSerializer, ApplicationStatusUpdateSerializer,
    NotificationSerializer, HourLogSerializer, FeedbackSerializer
)
from .permissions import IsVolunteer, IsOrganization, IsOrgOwnerOfOpportunity, IsOrgOwnerViaApplication
from .services import haversine_km

# Authentication / registration

class RegisterVolunteerView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterVolunteerSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class RegisterOrgView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterOrgSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

# Profiles

class MyVolunteerProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsVolunteer]
    serializer_class = VolunteerProfileSerializer

    def get_object(self):
        return self.request.user.volunteer_profile


class MyOrgProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsOrganization]
    serializer_class = OrganizationProfileSerializer

    def get_object(self):
        return self.request.user.org_profile


#  Opportunities (organization crud) 

class OpportunityCreateListView(generics.ListCreateAPIView):

    serializer_class = OpportunitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Opportunity.objects.select_related("organization", "organization__user").all().order_by("-created_at")
        mine = self.request.query_params.get("mine")
        if mine == "1" and hasattr(self.request.user, "org_profile"):
            qs = qs.filter(organization=self.request.user.org_profile)
        return qs

    def post(self, request, *args, **kwargs):
        if request.user.role != User.Role.ORG:
            return Response({"detail": "Only organizations can create opportunities."}, status=status.HTTP_403_FORBIDDEN)
        return super().post(request, *args, **kwargs)


class OpportunityRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OpportunitySerializer
    permission_classes = [IsAuthenticated, IsOrganization, IsOrgOwnerOfOpportunity]
    queryset = Opportunity.objects.select_related("organization", "organization__user").all()


# Search(volunteer)
class OpportunitySearchView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OpportunitySerializer

    def get_queryset(self):
        qs = Opportunity.objects.select_related("organization").all().order_by("-created_at")

        skill = self.request.query_params.get("skill")
        start = self.request.query_params.get("start")
        end = self.request.query_params.get("end")

        if start and end:
            qs = qs.filter(start_date__lte=end, end_date__gte=start)

        # Basic JSON contains match
        if skill:
            qs = qs.filter(Q(required_skills__icontains=skill))

        # Radius filtering
        lat = self.request.query_params.get("lat")
        lng = self.request.query_params.get("lng")
        radius_km = self.request.query_params.get("radius_km")
        if lat and lng and radius_km:
            try:
                latf = float(lat); lngf = float(lng); r = float(radius_km)
                filtered_ids = []
                for opp in qs:
                    if opp.latitude is None or opp.longitude is None:
                        continue
                    if haversine_km(latf, lngf, opp.latitude, opp.longitude) <= r:
                        filtered_ids.append(opp.id)
                qs = qs.filter(id__in=filtered_ids)
            except ValueError:
                pass

        # DRF search param for title/description
        q = self.request.query_params.get("search")
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(location_text__icontains=q))

        return qs


# Apply + status (volunteer + organization) 

class ApplyToOpportunityView(APIView):
    permission_classes = [IsAuthenticated, IsVolunteer]

    def post(self, request, opportunity_id: int):
        volunteer = request.user.volunteer_profile
        try:
            opp = Opportunity.objects.select_related("organization", "organization__user").get(id=opportunity_id)
        except Opportunity.DoesNotExist:
            return Response({"detail": "Opportunity not found."}, status=status.HTTP_404_NOT_FOUND)

        app, created = Application.objects.get_or_create(opportunity=opp, volunteer=volunteer)

        if created:
            # Notify organization on new application
            Notification.objects.create(
                user=opp.organization.user,
                type="APPLICATION_CREATED",
                title="New volunteer application",
                message=f"{volunteer.user.username} applied to '{opp.title}'.",
            )

        return Response(ApplicationSerializer(app).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class MyApplicationsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsVolunteer]
    serializer_class = ApplicationSerializer

    def get_queryset(self):
        return Application.objects.select_related("opportunity", "opportunity__organization").filter(
            volunteer=self.request.user.volunteer_profile
        ).order_by("-applied_at")


class OpportunityApplicantsView(generics.ListAPIView):    
    permission_classes = [IsAuthenticated, IsOrganization]
    serializer_class = ApplicationSerializer

    def get_queryset(self):
        opp_id = self.kwargs["opportunity_id"]
        return Application.objects.select_related("opportunity", "opportunity__organization").filter(
            opportunity_id=opp_id,
            opportunity__organization=self.request.user.org_profile
        ).order_by("-applied_at")


class UpdateApplicationStatusView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsOrganization, IsOrgOwnerViaApplication]
    queryset = Application.objects.select_related(
        "volunteer", "volunteer__user",
        "opportunity", "opportunity__organization", "opportunity__organization__user"
    ).all()
    serializer_class = ApplicationStatusUpdateSerializer

    def perform_update(self, serializer):
        app = self.get_object()
        updated = serializer.save()

        # Notify volunteer when status changes
        Notification.objects.create(
            user=app.volunteer.user,
            type="APPLICATION_STATUS_CHANGED",
            title="Application status updated",
            message=f"Your application for '{app.opportunity.title}' is now {updated.status}.",
        )


# Notifications

class MyNotificationsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by("-created_at")


class MarkNotificationReadView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def patch(self, request, *args, **kwargs):
        notif = self.get_object()
        if notif.user_id != request.user.id:
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        notif.is_read = True
        notif.save()
        return Response(NotificationSerializer(notif).data)


# Hours tracking

class LogHoursView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsVolunteer]
    serializer_class = HourLogSerializer

    def perform_create(self, serializer):
        app_id = self.request.data.get("application")
        app = Application.objects.select_related("volunteer", "volunteer__user").filter(id=app_id).first()
        if not app or app.volunteer.user_id != self.request.user.id:
            raise PermissionError("You can only log hours for your own applications.")
        serializer.save()


class MyHoursView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsVolunteer]
    serializer_class = HourLogSerializer

    def get_queryset(self):
        return HourLog.objects.select_related("application", "application__opportunity").filter(
            application__volunteer=self.request.user.volunteer_profile
        ).order_by("-work_date")


# Feedback (organization after completion) 

class LeaveFeedbackView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsOrganization]
    serializer_class = FeedbackSerializer

    def perform_create(self, serializer):
        org = self.request.user.org_profile
        app_id = self.request.data.get("application")
        app = Application.objects.select_related("opportunity", "opportunity__organization", "volunteer", "volunteer__user").filter(id=app_id).first()

        if not app or app.opportunity.organization_id != org.id:
            raise PermissionError("You can only leave feedback for your own opportunity applications.")

        feedback = serializer.save(organization=org)

        # Notify volunteer
        Notification.objects.create(
            user=app.volunteer.user,
            type="FEEDBACK_LEFT",
            title="Feedback received",
            message=f"{org.name} left feedback for '{app.opportunity.title}'. Rating: {feedback.rating}/5",
        )
