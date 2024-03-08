from directory.models import Coop, Person
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

class TestPeopleCreate(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # call_command('create_countries')
        # call_command('create_states')
        pass
    
    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', email='test@example.com', password='admin')
        #self.token = Token.objects.create(user=self.user)
        #self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key) 

        test_coop = Coop.objects.create(
            name = "Test People 1",
            enabled = True,
            web_site = "http://example.com",
            description = "This is a description",
            approved = False,
            rec_updated_by = self.user
        )
        test_coop.save()
        self.test_coop_id = test_coop.id

    def test_create_full(self):
        self.client.login(username='admin', password='admin')
        before_model_count = Person.objects.count()
        url = reverse('person-list')
        request = {
            "first_name": "Jeff",
            "last_name": "Doe",
            "coops": [ self.test_coop_id ],
            "contact_methods": [ 
                { "type": "PHONE", "is_public": True, "phone": "+17737777777"},
                { "type": "EMAIL", "is_public": True, "email": "jeffdoe@example.com"}
            ],
            "is_public": False
        }
        
        response = self.client.post(url, request, format='json')

        new_model_count = before_model_count + 1
        try:
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Person.objects.count(), new_model_count) 

            new_person = Person.objects.get(pk=response.data['id'])
            self.assertEqual(new_person.first_name, request['first_name'])
            self.assertEqual(new_person.last_name, request['last_name'])
            self.assertEqual(new_person.coops.count(), 1)
            self.assertIn(self.test_coop_id, new_person.coops.values_list('id', flat=True))
            self.assertEqual(new_person.is_public, False)
            self.assertEqual(new_person.contact_methods.count(), 2)
            self.assertIn( request["contact_methods"][0]["phone"], new_person.contact_methods.values_list('phone', flat=True))
            self.assertIn( request["contact_methods"][1]["email"], new_person.contact_methods.values_list('email', flat=True))

        except:
            print(response.data)
            raise
    
    def test_create_without_contactmethods(self):
        self.client.login(username='admin', password='admin')
        before_model_count = Person.objects.count()
        url = reverse('person-list')
        request = {
            "first_name": "Jeff",
            "last_name": "Doe",
            "coops": [ self.test_coop_id ],
            "contact_methods": [],
            "is_public": False
        }
        
        response = self.client.post(url, request, format='json')

        new_model_count = before_model_count + 1
        try:
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Person.objects.count(), new_model_count) 

            new_person = Person.objects.get(pk=response.data['id'])
            self.assertEqual(new_person.first_name, request['first_name'])
            self.assertEqual(new_person.last_name, request['last_name'])
            self.assertEqual(new_person.coops.count(), 1)
            self.assertIn(self.test_coop_id, new_person.coops.values_list('id', flat=True))
            self.assertEqual(new_person.is_public, False)
            self.assertEqual(new_person.contact_methods.count(), 0)
        except:
            print(response.data)
            raise


    def test_create_undefined_contactmethods(self):
        self.client.login(username='admin', password='admin')
        before_model_count = Person.objects.count()
        url = reverse('person-list')
        request = {
            "first_name": "Jeff",
            "last_name": "Doe",
            "coops": [ self.test_coop_id ],
            "is_public": False
        }
        
        response = self.client.post(url, request, format='json')

        try:
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(Person.objects.count(), before_model_count) 
        except:
            print(response.data)
            raise

    def test_create_without_coops(self):
        self.client.login(username='admin', password='admin')
        before_model_count = Person.objects.count()
        url = reverse('person-list')
        request = {
            "first_name": "Jeff",
            "last_name": "Doe",
            "coops": [ ],
            "contact_methods": [
                { "type": "PHONE", "is_public": True, "phone": "+17737777777"},
                { "type": "EMAIL", "is_public": True, "email": "jeffdoe@example.com"}],
            "is_public": False
        }
        
        response = self.client.post(url, request, format='json')

        try:
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(Person.objects.count(), before_model_count) 
        except:
            print(response.data)
            raise

    def test_create_undefined_coops(self):
        self.client.login(username='admin', password='admin')
        before_model_count = Person.objects.count()
        url = reverse('person-list')
        request = {
            "first_name": "Jeff",
            "last_name": "Doe",
            "contact_methods": [
                { "type": "PHONE", "is_public": True, "phone": "+17737777777"},
                { "type": "EMAIL", "is_public": True, "email": "jeffdoe@example.com"}],
            "is_public": False
        }
        
        response = self.client.post(url, request, format='json')

        try:
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(Person.objects.count(), before_model_count) 
        except:
            print(response.data)
            raise
