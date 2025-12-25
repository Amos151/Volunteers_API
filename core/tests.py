from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import User, VolunteerProfile, OrganizationProfile, Opportunity

class SmokeTests(APITestCase):
    def test_register_volunteer_and_get_token(self):
        res = self.client.post("/api/auth/register/volunteer/", {
            "username": "vol1",
            "email": "vol1@example.com",
            "password": "StrongPassw0rd!!",
            "skills": ["FirstAid", "Cleanup"],
            "location_text": "Port of Spain, Trinidad"
        }, format="json")
        self.assertIn(res.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])

        token = self.client.post("/api/auth/token/", {
            "username": "vol1",
            "password": "StrongPassw0rd!!"
        }, format="json")
        self.assertEqual(token.status_code, status.HTTP_200_OK)
        self.assertIn("access", token.data)

    def test_org_can_create_opportunity(self):
        # register organization
        self.client.post("/api/auth/register/org/", {
            "username": "org1",
            "email": "org1@example.com",
            "password": "StrongPassw0rd!!",
            "name": "Helping Hands"
        }, format="json")

        token = self.client.post("/api/auth/token/", {"username":"org1","password":"StrongPassw0rd!!"}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.data['access']}")

        res = self.client.post("/api/opportunities/", {
            "title": "Beach Cleanup",
            "description": "Help clean the coastline.",
            "required_skills": ["Cleanup"],
            "location_text": "Maracas Beach, Trinidad",
            "start_date": "2025-12-28",
            "end_date": "2025-12-28"
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
