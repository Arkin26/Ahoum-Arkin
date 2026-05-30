from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import Profile
from apps.accounts.otp import store_otp


class AuthFlowTests(APITestCase):
    def test_signup_verify_login(self):
        signup = self.client.post(
            reverse("auth-signup"),
            {"email": "new@ahoum.com", "password": "Test1234!", "role": "seeker"},
            format="json",
        )
        self.assertEqual(signup.status_code, status.HTTP_201_CREATED)

        store_otp("new@ahoum.com", "123456")
        verify = self.client.post(
            reverse("auth-verify-email"),
            {"email": "new@ahoum.com", "otp": "123456"},
            format="json",
        )
        self.assertEqual(verify.status_code, status.HTTP_200_OK)

        login = self.client.post(
            reverse("auth-login"),
            {"email": "new@ahoum.com", "password": "Test1234!"},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertIn("access", login.data)

    def test_unverified_login_blocked(self):
        User.objects.create_user(
            username="blocked@ahoum.com",
            email="blocked@ahoum.com",
            password="Test1234!",
            is_active=False,
        )
        Profile.objects.create(user=User.objects.get(email="blocked@ahoum.com"), role="seeker")

        login = self.client.post(
            reverse("auth-login"),
            {"email": "blocked@ahoum.com", "password": "Test1234!"},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_400_BAD_REQUEST)

    def test_signup_rejects_username(self):
        response = self.client.post(
            reverse("auth-signup"),
            {
                "email": "x@ahoum.com",
                "password": "Test1234!",
                "role": "seeker",
                "username": "bad",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
