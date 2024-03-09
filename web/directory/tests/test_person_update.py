from directory.models import Coop, ContactMethod, Person
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from . import helpers

class TestPersonUpdate(APITestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):
        self.creating_user = User.objects.create_superuser(username='admin', email='test@example.com', password='admin')

        test_coop_1 = Coop.objects.create(
            name = "Test People Update 1",
            enabled = True,
            web_site = "http://example.com",
            description = "This is a description",
            approved = False,
            rec_updated_by = self.creating_user
        )
        test_coop_1.save()
        self.test_coop_1_id = test_coop_1.id

        test_coop_2 = Coop.objects.create(
            name = "Test People Update 2",
            enabled = True,
            web_site = "http://example.com",
            description = "This is a description",
            approved = False,
            rec_updated_by = self.creating_user
        )
        test_coop_2.save()
        self.test_coop_2_id = test_coop_2.id

        test_person_cm_1 = ContactMethod.objects.create( is_public = False, type = "EMAIL", email = "exampleaddress9@example.com"  )
        test_person_cm_2 = ContactMethod.objects.create( is_public = False, type = "PHONE", phone = "+13122222222"  )
        test_person_cm_3 = ContactMethod.objects.create( is_public = False, type = "PHONE", phone = "+13123333333"  )
        test_person = Person.objects.create( first_name = "Jane", last_name = "Smith", is_public = False)
        test_person.contact_methods.set([test_person_cm_1, test_person_cm_2, test_person_cm_3])
        test_coop_1.people.set([test_person])
        test_person.save()
        self.test_person_id = test_person.id

        # Authenticating as admin user for all tests in class
        self.modifying_user = User.objects.create_superuser(username='testuser', email='test2@example.com', password='password')
        self.token = helpers.obtain_jwt_token("testuser", "password")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_update_basic(self):
        before_person_count = Person.objects.count()
        before_coop_count = Coop.objects.count()
        before_contactmethod_count = ContactMethod.objects.count()
        instance = Person.objects.get(pk=self.test_person_id)

        url = reverse('person-detail', args=[self.test_person_id])
        request = {
            "first_name": "James",
            "last_name": "Doe-Smith",
            "is_public": True
        }

        response = self.client.patch(url, request, format='json')

        try:
            # Validate successful HTTP response
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Validate acting as modifying_user
            self.assertEquals(self.client._credentials['HTTP_AUTHORIZATION'], f'Bearer {self.token}')
            # Validate number of instances
            self.assertEqual(Person.objects.count(), before_person_count)
            self.assertEqual(Coop.objects.count(), before_coop_count)
            self.assertEqual(ContactMethod.objects.count(), before_contactmethod_count)
            # Validate contents of modified instance
            modified_person = Person.objects.get(pk=response.data['id'])
            self.assertEqual(modified_person.first_name, request["first_name"])
            self.assertEqual(modified_person.last_name, request["last_name"])
            self.assertEqual(modified_person.is_public, request["is_public"])
            self.assertEqual(modified_person.contact_methods.count(), instance.contact_methods.count())
        except:
            print(response.data)
            raise
    
    def test_update_without_contactmethods(self):
        before_person_count = Person.objects.count()
        before_coop_count = Coop.objects.count()
        before_contactmethod_count = ContactMethod.objects.count()
        instance = Person.objects.get(pk=self.test_person_id)

        url = reverse('person-detail', args=[self.test_person_id])
        request = {
            "first_name": "James",
            "last_name": "Doe-Smith",
            "is_public": True,
            "contact_methods": []
        }

        response = self.client.patch(url, request, format='json')

        try:
            # Validate successful HTTP response
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Validate acting as modifying_user
            self.assertEquals(self.client._credentials['HTTP_AUTHORIZATION'], f'Bearer {self.token}')
            # Validate number of instances
            self.assertEqual(Person.objects.count(), before_person_count)
            self.assertEqual(Coop.objects.count(), before_coop_count)
            self.assertEqual(ContactMethod.objects.count(), before_contactmethod_count-3)
            # Validate contents of modified instance
            modified_person = Person.objects.get(pk=response.data['id'])
            self.assertEqual(modified_person.first_name, request["first_name"])
            self.assertEqual(modified_person.last_name, request["last_name"])
            self.assertEqual(modified_person.is_public, request["is_public"])
            self.assertEqual(modified_person.contact_methods.count(), 0)
        except:
            print(response.data)
            raise

    def test_update_with_contactmethods(self):
        before_person_count = Person.objects.count()
        before_coop_count = Coop.objects.count()
        before_contactmethod_count = ContactMethod.objects.count()
        instance = Person.objects.get(pk=self.test_person_id)

        url = reverse('person-detail', args=[self.test_person_id])
        request = {
            "first_name": "James",
            "last_name": "Doe-Smith",
            "is_public": True,
            "contact_methods": [
                { "type": "EMAIL", "is_public": True, "email": "test_person_update_1@example.com" },
                { "type": "EMAIL", "is_public": True, "email": "test_person_update_2@example.com" },
                { "type": "PHONE", "is_public": True, "phone": "+13128888888" },
                { "type": "PHONE", "is_public": True, "phone": "+13129999999" }
            ]
        }

        response = self.client.patch(url, request, format='json')

        try:
            # Validate successful HTTP response
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Validate acting as modifying_user
            self.assertEquals(self.client._credentials['HTTP_AUTHORIZATION'], f'Bearer {self.token}')
            # Validate number of instances
            self.assertEqual(Person.objects.count(), before_person_count)
            self.assertEqual(Coop.objects.count(), before_coop_count)
            self.assertEqual(ContactMethod.objects.count(), before_contactmethod_count-3+4)  #removes 3 existing, adds 4 in request
            # Validate contents of modified instance
            modified_person = Person.objects.get(pk=response.data['id'])
            self.assertEqual(modified_person.first_name, request["first_name"])
            self.assertEqual(modified_person.last_name, request["last_name"])
            self.assertEqual(modified_person.is_public, request["is_public"])
            self.assertEqual(modified_person.contact_methods.count(), 4)
            self.assertIn( request["contact_methods"][0]["email"], modified_person.contact_methods.values_list('email', flat=True))
            self.assertIn( request["contact_methods"][1]["email"], modified_person.contact_methods.values_list('email', flat=True))
            self.assertIn( request["contact_methods"][2]["phone"], modified_person.contact_methods.values_list('phone', flat=True))
            self.assertIn( request["contact_methods"][3]["phone"], modified_person.contact_methods.values_list('phone', flat=True))
        except:
            print(response.data)
            raise
    
    def test_update_without_coops(self):
        before_person_count = Person.objects.count()
        before_coop_count = Coop.objects.count()
        before_contactmethod_count = ContactMethod.objects.count()
        instance = Person.objects.get(pk=self.test_person_id)

        url = reverse('person-detail', args=[self.test_person_id])
        request = {
            "first_name": "James",
            "last_name": "Doe-Smith",
            "is_public": True,
            "coops": []
        }

        response = self.client.patch(url, request, format='json')

        try:
            # Validate successful HTTP response
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            # Validate acting as modifying_user
            self.assertEquals(self.client._credentials['HTTP_AUTHORIZATION'], f'Bearer {self.token}')
            # Validate that no instances were created
            self.assertEqual(Person.objects.count(), before_person_count)
            self.assertEqual(Coop.objects.count(), before_coop_count)
            self.assertEqual(ContactMethod.objects.count(), before_contactmethod_count)
        except:
            print(response.data)
            raise
    
    def test_update_with_coops(self):
        before_person_count = Person.objects.count()
        before_coop_count = Coop.objects.count()
        before_contactmethod_count = ContactMethod.objects.count()
        instance = Person.objects.get(pk=self.test_person_id)

        url = reverse('person-detail', args=[self.test_person_id])
        request = {
            "first_name": "James",
            "last_name": "Doe-Smith",
            "is_public": True,
            "coops": [ self.test_coop_2_id ]
        }

        response = self.client.patch(url, request, format='json')

        try:
            # Validate successful HTTP response
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Validate acting as modifying_user
            self.assertEquals(self.client._credentials['HTTP_AUTHORIZATION'], f'Bearer {self.token}')
            # Validate number of instances
            self.assertEqual(Person.objects.count(), before_person_count)
            self.assertEqual(Coop.objects.count(), before_coop_count)
            self.assertEqual(ContactMethod.objects.count(), before_contactmethod_count)
            # Validate contents of modified instance
            modified_person = Person.objects.get(pk=response.data['id'])
            self.assertEqual(modified_person.first_name, request["first_name"])
            self.assertEqual(modified_person.last_name, request["last_name"])
            self.assertEqual(modified_person.is_public, request["is_public"])
            self.assertEqual(modified_person.contact_methods.count(), 3)
            self.assertEqual(modified_person.coops.count(), 1)
            self.assertIn( self.test_coop_2_id, modified_person.coops.values_list('id', flat=True))
        except:
            print(response.data)
            raise
