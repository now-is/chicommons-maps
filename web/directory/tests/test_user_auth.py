from directory.models import Coop, ContactMethod, Person
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from . import helpers

class TestPeopleUpdate(APITestCase):
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