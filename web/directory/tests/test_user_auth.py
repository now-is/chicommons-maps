from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from . import helpers

class TestUserAuth(APITestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass')

    def test_login_successful(self):
        url = reverse('token_obtain_pair')
        request = {
            "username": "testuser",
            "password": "testpass"
        }
        response = self.client.post(url, request, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('refresh', response.data)
        self.assertIn('access', response.data)

    def test_login_unsuccessful(self):
        url = reverse('token_obtain_pair')
        request = {
            "username": "testuser",
            "password": "xxxxxxxxxxxx"
        }
        response = self.client.post(url, request, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_endpoint_successful(self):
        client = APIClient()
        token = helpers.obtain_jwt_token("testuser", "testpass")
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        url = reverse('coop-list')
        response = client.get(url, data={}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_endpoint_unsuccessful(self):
        client = APIClient()
        token = helpers.obtain_jwt_token("testuser", "xxxxxxxxxxxx")
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        url = reverse('coop-list')
        response = client.get(url, data={}, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class TestUserRegistration(APITestCase):
    def test_user_registration(self):
        url = reverse('register')
        request = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'password'
        }
        response = self.client.post(url, request, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='testuser').exists())
        self.assertTrue('access' in response.data)
        self.assertTrue('refresh' in response.data)

class PasswordResetRequestViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='old_password')
        self.url = reverse('password-reset-request')

    def test_password_reset_request(self):
        response = self.client.post(self.url, {'email': 'test@example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Password reset link has been sent to your email.', response.data['message'])

class PasswordResetConfirmViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='old_password')
        self.token_generator = PasswordResetTokenGenerator()
        self.token = self.token_generator.make_token(self.user)
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))  # Ensure this matches how your UID is generated/decoded in your views
        self.url = reverse('password-reset-confirm', args=[self.uid, self.token])

    def test_password_reset_confirm(self):
        new_password = 'new_password123'
        response = self.client.post(self.url, {'password': new_password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Password has been reset successfully.', response.data['message'])

        # Verify the password was actually changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))