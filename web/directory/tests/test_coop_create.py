from directory.models import Coop
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
import datetime

class TestCoopCreate(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # call_command('create_countries')
        # call_command('create_states')
        pass

    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', email='test@example.com', password='admin')
        #self.token = Token.objects.create(user=self.user)
        #self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_create_full(self):
        self.client.login(username='admin', password='admin')
        before_model_count = Coop.objects.count()
        url = reverse('coop-list')
        request = {
            "name": "Test Dave 9999",
            "types": [ {"name": "Library"} ],
            "enabled": True,
            "contact_methods": [
                { "type": "EMAIL", "is_public": True, "email": "myemail@example.com" },
                { "type": "PHONE", "is_public": True, "phone": "+17739441426" }          
            ],
            "web_site": "http://www.1871.com/",
            "description": "My Coop Description",
            "approved": True, # TODO - Confirm biz logic. Should you be able to approve the Coop create in the same call you create it?
            "proposed_changes": { "description": "Testing testing testing." },
            "reject_reason": "This is sample data.",
            "coop_public": False,
            "status": "Testing", #TODO - What are acceptable values?
            "scope": "Testing", #TODO - What are acceptable values?
            "tags": "tag1, tag2, tag3", #TODO - What are acceptable values?
            "rec_source": "Testing", #TODO - What are acceptable values?
            "rec_updated_by": 2, #TODO - Should you be able to overload this?
            "rec_updated_date": "1996-03-31T18:30:00", #TODO - Should you be able to overload this?
            "coop_address_tags": [
                {
                    "is_public": True,
                    "address": {
                        "street_address": "222 W. Merchandise Mart Plaza, Suite 1212",
                        "city": "Chicago",
                        "state": "IL",
                        "postal_code": "60654",
                        "country": "US"
                    }
                }
            ],
            "people": [
                {"first_name": "John", "last_name": "Doe", "is_public": False, "contact_methods": []}, 
                {"first_name": "Steve", "last_name": "Smith", "is_public": False, "contact_methods": [
                    { "type": "EMAIL", "is_public": True, "email": "stevesmith@example.com" }
                ],
                
                }
            ]
        }
        # req_json = json.dumps(request)
        # print(req_json)
        
        response = self.client.post(url, request, format='json')

        new_model_count = before_model_count + 1
        try:
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Coop.objects.count(), new_model_count) 

            new_coop = Coop.objects.get(pk=response.data['id'])
            self.assertEqual(new_coop.name, request['name'])
            self.assertEqual(new_coop.types.count(), len(request["types"]))
            self.assertEqual(new_coop.coop_address_tags.count(), len(request["coop_address_tags"]))
            self.assertEqual(new_coop.people.count(), len(request["people"]))
            self.assertEqual(new_coop.contact_methods.count(), len(request["contact_methods"]))
            self.assertEqual(new_coop.approved, request['approved'])
            self.assertEqual(new_coop.rec_updated_by.id, self.user.id)
            self.assertNotEqual(new_coop.rec_updated_date, datetime.datetime.strptime( request["rec_updated_date"], "%Y-%m-%dT%H:%M:%S"))
        except:
            print(response.data)
            raise

    def test_create_minimum(self):
        self.client.login(username='admin', password='admin')
        before_model_count = Coop.objects.count()
        url = reverse('coop-list')
        request = {
            "name": "Test Dave 9999", 
            "types": [ {"name": "Library"} ],
            "enabled": True, 
            "web_site": "http://www.1871.com/"
        }

        response = self.client.post(url, request, format='json')

        new_model_count = before_model_count + 1
        try:
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Coop.objects.count(), new_model_count) 
            new_coop = Coop.objects.get(pk=response.data['id'])
            self.assertEqual(new_coop.name, request['name'])
            self.assertEqual(new_coop.types.count(), len(request["types"]))
            self.assertEqual(new_coop.coop_address_tags.count(), 0)
            self.assertEqual(new_coop.people.count(), 0)
            self.assertEqual(new_coop.contact_methods.count(), 0)

            self.assertEqual(new_coop.approved, False)
            self.assertIsNone(new_coop.proposed_changes)
            self.assertIsNone(new_coop.reject_reason)
            self.assertIsInstance(new_coop.rec_updated_date, datetime.datetime)
            self.assertEqual(new_coop.rec_updated_by.username, self.user.username)
        except:
            print(response.data)
            raise
            
    def test_create_empty(self):
        self.client.login(username='admin', password='admin')
        before_model_count = Coop.objects.count()
        url = reverse('coop-list')
        request = {
            "name": "Test Dave 9999", 
            "types": [ {"name": "Library"} ],
            "enabled": True, 
            "description": "My Coop Description", 
            "web_site": "http://www.1871.com/",
            "coop_address_tags": [],
            "people": [],
            "contact_methods": []
        }

        response = self.client.post(url, request, format='json')

        new_model_count = before_model_count + 1
        try:
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Coop.objects.count(), new_model_count) 
            new_coop = Coop.objects.get(pk=response.data['id'])
            self.assertEqual(new_coop.name, request['name'])
            self.assertEqual(new_coop.types.count(), len(request["types"]))
            self.assertEqual(new_coop.coop_address_tags.count(), len(request["coop_address_tags"]))
            self.assertEqual(new_coop.people.count(), len(request["people"]))
            self.assertEqual(new_coop.contact_methods.count(), len(request["contact_methods"]))

            self.assertEqual(new_coop.approved, False)
            self.assertIsNone(new_coop.proposed_changes)
            self.assertIsNone(new_coop.reject_reason)
            self.assertIsInstance(new_coop.rec_updated_date, datetime.datetime)
            self.assertEqual(new_coop.rec_updated_by.username, self.user.username)
        except:
            print(response.data)
            raise
    
    def test_create_with_contactmethod(self):
        self.client.login(username='admin', password='admin')
        before_model_count = Coop.objects.count()
        url = reverse('coop-list')
        request = {
            "name": "Test Dave 9999", 
            "types": [ {"name": "Library"} ],
            "enabled": True, 
            "description": "My Coop Description", 
            "web_site": "http://www.1871.com/",
            "coop_address_tags": [],
            "people": [],
            "contact_methods": [
                {
                "type": "EMAIL",
                "is_public": True,
                "email": "myemail@example.com"
                },
                {
                "type": "PHONE",
                "is_public": True,
                "phone": "+17739441426"
                }          
            ]
        }

        response = self.client.post(url, request, format='json')

        new_model_count = before_model_count + 1
        try:
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Coop.objects.count(), new_model_count) 
            new_coop = Coop.objects.get(pk=response.data['id'])
            self.assertEqual(new_coop.name, request['name'])
            self.assertEqual(new_coop.types.count(), len(request["types"]))
            self.assertEqual(new_coop.coop_address_tags.count(), len(request["coop_address_tags"]))
            self.assertEqual(new_coop.people.count(), len(request["people"]))
            self.assertEqual(new_coop.contact_methods.count(), len(request["contact_methods"]))

            self.assertEqual(new_coop.approved, False)
            self.assertIsNone(new_coop.proposed_changes)
            self.assertIsNone(new_coop.reject_reason)
            self.assertIsInstance(new_coop.rec_updated_date, datetime.datetime)
            self.assertEqual(new_coop.rec_updated_by.username, self.user.username)
        except:
            print(response.data)
            raise

    def test_create_with_address(self):
        self.client.login(username='admin', password='admin')
        before_model_count = Coop.objects.count()
        url = reverse('coop-list')
        request = {
            "name": "Test Dave 9999", 
            "types": [ {"name": "Library"} ],
            "enabled": True, 
            "description": "My Coop Description", 
            "web_site": "http://www.1871.com/",
            "coop_address_tags": [
                {
                    "is_public": True,
                    "address": {
                        "street_address": "222 W. Merchandise Mart Plaza, Suite 1212",
                        "city": "Chicago",
                        "state": "IL",
                        "postal_code": "60654",
                        "country": "US"
                    }
                },
                {
                    "is_public": True,
                    "address": {
                        "street_address": "123 Main Street",
                        "city": "Chicago",
                        "state": "IL",
                        "postal_code": "60654",
                        "country": "US"
                    }
                }
            ],
            "people": [],
            "contact_methods": []
        }

        response = self.client.post(url, request, format='json')

        new_model_count = before_model_count + 1 
        try:
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Coop.objects.count(), new_model_count) 
            new_coop = Coop.objects.get(pk=response.data['id'])
            self.assertEqual(new_coop.name, request['name'])
            self.assertEqual(new_coop.types.count(), len(request["types"]))
            self.assertEqual(new_coop.coop_address_tags.count(), len(request["coop_address_tags"]))
            self.assertEqual(new_coop.people.count(), len(request["people"]))
            self.assertEqual(new_coop.contact_methods.count(), len(request["contact_methods"]))
            
            self.assertEqual(new_coop.approved, False)
            self.assertIsNone(new_coop.proposed_changes)
            self.assertIsNone(new_coop.reject_reason)
            self.assertIsInstance(new_coop.rec_updated_date, datetime.datetime)
            self.assertEqual(new_coop.rec_updated_by.username, self.user.username)
        except:
            print(response.data)
            raise
    
    def test_create_with_people(self):
        self.client.login(username='admin', password='admin')
        before_model_count = Coop.objects.count()
        url = reverse('coop-list')
        request = {
            "name": "Test Dave 9999", 
            "types": [ {"name": "Library"} ],
            "enabled": True, 
            "description": "My Coop Description", 
            "web_site": "http://www.1871.com/",
            "coop_address_tags": [],
            "people": [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "contact_methods": [],
                    "is_public": False
                }, 
                {
                    "first_name": "Steve",
                    "last_name": "Smith",
                    "contact_methods": [
                        {
                        "type": "EMAIL",
                        "is_public": True,
                        "email": "stevesmith@example.com"
                        }
                    ],
                    "is_public": False
                }
            ],
            "contact_methods": []
        }

        response = self.client.post(url, request, format='json')

        new_model_count = before_model_count + 1
        try:
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Coop.objects.count(), new_model_count) 
            new_coop = Coop.objects.get(pk=response.data['id'])
            self.assertEqual(new_coop.name, request['name'])
            self.assertEqual(new_coop.types.count(), len(request["types"]))
            self.assertEqual(new_coop.coop_address_tags.count(), len(request["coop_address_tags"]))
            self.assertEqual(new_coop.people.count(), len(request["people"]))
            self.assertEqual(new_coop.contact_methods.count(), len(request["contact_methods"]))

            self.assertEqual(new_coop.approved, False)
            self.assertIsNone(new_coop.proposed_changes)
            self.assertIsNone(new_coop.reject_reason)
            self.assertIsInstance(new_coop.rec_updated_date, datetime.datetime)
            self.assertEqual(new_coop.rec_updated_by.username, self.user.username)
        except:
            print(response.data)
            raise
