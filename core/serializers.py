from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import (
    User, VolunteerProfile, OrganizationProfile,
    Opportunity, Application, Notification, HourLog, Feedback
)
from .services import geocode_location

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role"]


class VolunteerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = VolunteerProfile
        fields = ["id", "user", "location_text", "latitude", "longitude", "skills", "availability"]

    def update(self, instance, validated_data):
        location_text = validated_data.get("location_text", instance.location_text)
        instance.location_text = location_text
        instance.skills = validated_data.get("skills", instance.skills)
        instance.availability = validated_data.get("availability", instance.availability)

        # If location updated, re-geocode
        if "location_text" in validated_data:
            lat, lng = geocode_location(location_text)
            instance.latitude = lat
            instance.longitude = lng

        instance.save()
        return instance


class OrganizationProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = OrganizationProfile
        fields = ["id", "user", "name", "mission", "contact_phone", "location_text", "latitude", "longitude"]

    def update(self, instance, validated_data):
        for f in ["name", "mission", "contact_phone"]:
            if f in validated_data:
                setattr(instance, f, validated_data[f])

        if "location_text" in validated_data:
            instance.location_text = validated_data["location_text"]
            lat, lng = geocode_location(instance.location_text)
            instance.latitude = lat
            instance.longitude = lng

        instance.save()
        return instance


class RegisterVolunteerSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    location_text = serializers.CharField(required=False, allow_blank=True)
    skills = serializers.ListField(child=serializers.CharField(), required=False)
    availability = serializers.DictField(required=False)

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            role=User.Role.VOLUNTEER
        )
        loc = validated_data.get("location_text", "")
        lat, lng = geocode_location(loc) if loc else (None, None)
        VolunteerProfile.objects.create(
            user=user,
            location_text=loc,
            latitude=lat,
            longitude=lng,
            skills=validated_data.get("skills", []),
            availability=validated_data.get("availability", {}),
        )
        return user


class RegisterOrgSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    name = serializers.CharField()
    mission = serializers.CharField(required=False, allow_blank=True)
    contact_phone = serializers.CharField(required=False, allow_blank=True)
    location_text = serializers.CharField(required=False, allow_blank=True)

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            role=User.Role.ORG
        )
        loc = validated_data.get("location_text", "")
        lat, lng = geocode_location(loc) if loc else (None, None)
        OrganizationProfile.objects.create(
            user=user,
            name=validated_data["name"],
            mission=validated_data.get("mission", ""),
            contact_phone=validated_data.get("contact_phone", ""),
            location_text=loc,
            latitude=lat,
            longitude=lng,
        )
        return user


class OpportunitySerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = Opportunity
        fields = [
            "id", "organization", "organization_name",
            "title", "description", "required_skills",
            "location_text", "latitude", "longitude",
            "start_date", "end_date", "created_at",
        ]
        read_only_fields = ["organization", "latitude", "longitude", "created_at"]

    def create(self, validated_data):
        request = self.context["request"]
        org_profile = request.user.org_profile
        validated_data["organization"] = org_profile

        # geocode if location provided
        loc = validated_data.get("location_text", "")
        if loc:
            lat, lng = geocode_location(loc)
            validated_data["latitude"] = lat
            validated_data["longitude"] = lng

        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "location_text" in validated_data:
            loc = validated_data["location_text"]
            lat, lng = geocode_location(loc) if loc else (None, None)
            instance.latitude = lat
            instance.longitude = lng
        return super().update(instance, validated_data)


class ApplicationSerializer(serializers.ModelSerializer):
    opportunity_title = serializers.CharField(source="opportunity.title", read_only=True)
    org_name = serializers.CharField(source="opportunity.organization.name", read_only=True)

    class Meta:
        model = Application
        fields = ["id", "opportunity", "opportunity_title", "org_name", "status", "applied_at", "updated_at"]
        read_only_fields = ["status", "applied_at", "updated_at"]


class ApplicationStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ["status"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "type", "title", "message", "is_read", "created_at"]


class HourLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = HourLog
        fields = ["id", "application", "work_date", "hours", "note", "created_at"]
        read_only_fields = ["created_at"]

    def validate(self, attrs):
        # Volunteer can only log hours for their own application (enforced in views too)
        return attrs


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ["id", "application", "organization", "rating", "comment", "created_at"]
        read_only_fields = ["organization", "created_at"]
