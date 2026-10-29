from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AccountsTests(TestCase):
    def test_registration_page_loads(self):
        response = self.client.get(reverse("register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create an Account")

    def test_user_can_register(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "testuser",
                "email": "test@example.com",
                "password1": "StrongPass!2026",
                "password2": "StrongPass!2026",
            },
        )

        self.assertTrue(
            User.objects.filter(username="testuser").exists()
        )
        self.assertRedirects(response, reverse("login"))

    def test_login_page_loads(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)

    def test_user_can_login(self):
        User.objects.create_user(
            username="testuser",
            password="StrongPass!2026",
        )

        response = self.client.post(
            reverse("login"),
            {
                "username": "testuser",
                "password": "StrongPass!2026",
            },
        )

        self.assertRedirects(response, "/projects/")
        self.assertIn("_auth_user_id", self.client.session)

    def test_user_can_logout(self):
        user = User.objects.create_user(
            username="testuser",
            password="StrongPass!2026",
        )
        self.client.force_login(user)

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)