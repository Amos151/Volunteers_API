from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class User(AbstractUser):
    class Role(models.TextChoices):
        VOLUNTEER = "VOLUNTEER", "Volunteer"
        ORG = "ORG", "Organization"
        ADMIN = "ADMIN", "Admin"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VOLUNTEER)

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"


class VolunteerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="volunteer_profile")
    location_text = models.CharField(max_length=255, blank=True, default="")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    skills = models.JSONField(default=list, blank=True)
    availability = models.JSONField(default=dict, blank=True)  

    def __str__(self) -> str:
        return f"VolunteerProfile<{self.user_id}>"


class OrganizationProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="org_profile")
    name = models.CharField(max_length=200)
    mission = models.TextField(blank=True, default="")
    contact_phone = models.CharField(max_length=50, blank=True, default="")

    location_text = models.CharField(max_length=255, blank=True, default="")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name


class Opportunity(models.Model):
    organization = models.ForeignKey(OrganizationProfile, on_delete=models.CASCADE, related_name="opportunities")
    title = models.CharField(max_length=200)
    description = models.TextField()
    required_skills = models.JSONField(default=list, blank=True)

    location_text = models.CharField(max_length=255, blank=True, default="")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.title} @ {self.organization.name}"


class Application(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name="applications")
    volunteer = models.ForeignKey(VolunteerProfile, on_delete=models.CASCADE, related_name="applications")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    applied_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["opportunity", "volunteer"], name="unique_application_per_volunteer")
        ]

    def __str__(self) -> str:
        return f"Application<{self.id}> {self.volunteer.user.username} -> {self.opportunity.title} ({self.status})"


class HourLog(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="hour_logs")
    work_date = models.DateField()
    hours = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    note = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)


class Feedback(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name="feedback")
    organization = models.ForeignKey(OrganizationProfile, on_delete=models.CASCADE, related_name="feedback_left")
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=50)  
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"Notification<{self.user_id}> {self.title}"
