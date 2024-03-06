from .models import Coop, CoopType, ContactMethod, Person, CoopAddressTags
from address.models import Address, Locality, AddressField, Country, State
from .serializers import AddressSerializer, CoopAddressTagsSerializer
from .services.location_service import LocationService
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
import datetime
import json
import requests
import urllib
from geopy.geocoders import Nominatim
from functools import partial

class CoopCreateTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('create_countries')
        call_command('create_states')

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
                        "raw": "222 W. Merchandise Mart Plaza, Suite 1212",
                        "formatted": "222 W. Merchandise Mart Plaza, Suite 1212",
                        "locality": "Chicago",
                        "state": "IL",
                        "postal_code": "60654",
                        "country": "United States"
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
                        "raw": "222 W. Merchandise Mart Plaza, Suite 1212",
                        "formatted": "222 W. Merchandise Mart Plaza, Suite 1212",
                        "locality": "Chicago",
                        "state": "IL",
                        "postal_code": "60654",
                        "country": "United States"
                    }
                },
                {
                    "is_public": True,
                    "address": {
                        "raw": "123 Main Street",
                        "formatted": "123 Main Street",
                        "locality": "Chicago",
                        "state": "IL",
                        "postal_code": "60654",
                        "country": "United States"
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
 
class CoopUpdateTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('create_countries')
        call_command('create_states')

    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', email='test@example.com', password='admin')
        self.modifying_user = User.objects.create_superuser(username='chicommons', email='test2@example.com', password='chicommons')
        #self.token = Token.objects.create(user=self.user)
        #self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # Create new Coop instance. Define Basic Fields.
        instance = Coop.objects.create(
            name = "Test Coop 1",
            enabled = True,
            web_site = "http://example.com",
            description = "This is a description",
            approved = False,
            rec_updated_by = self.user
        )
        # Define Array Field: types
        coop_types = [CoopType.objects.create( name = "Disco" )]
        instance.types.set(coop_types) 
        # Define Array Field: contact_methods
        contact_methods = [
            ContactMethod.objects.create( is_public = False, type = "EMAIL", email = "exampleaddress@example.com"  ),
            ContactMethod.objects.create( is_public = False, type = "EMAIL", email = "exampleaddress2@example.com"  ),
            ContactMethod.objects.create( is_public = False, type = "PHONE", phone = "+13125555555"  ),            
            ContactMethod.objects.create( is_public = False, type = "PHONE", phone = "+13127777777"  )
        ]
        instance.contact_methods.set(contact_methods)
        # Define Array Field: coop_address_tags
        address_data = {
            "raw": "233 S Wacker Dr",
            "formatted": "233 S Wacker Dr",
            "locality": "Chicago",
            "state": "IL",
            "postal_code": "60606",
            "country": "United States"
        }
        address_serializer = AddressSerializer(data=address_data)
        address_serializer.is_valid()
        addy_a = address_serializer.save()
        cat_a = CoopAddressTags.objects.create( is_public = False, address = addy_a )
        instance.coop_address_tags.set([])
        # Define Array Field: people
        person_a = Person.objects.create( first_name = "Jane", last_name = "Doe", is_public = False )
        person_b_cm_1 = ContactMethod.objects.create( is_public = False, type = "EMAIL", email = "exampleaddress2@example.com"  )
        person_b_cm_2 = ContactMethod.objects.create( is_public = False, type = "PHONE", phone = "+13128888888"  )
        person_b = Person.objects.create( first_name = "Jane", last_name = "Smith", is_public = False)
        person_b.contact_methods.set([person_b_cm_1, person_b_cm_2])
        instance.people.set([person_a, person_b])
        # Save new Instance
        instance.save()
        self.instance_id = instance.id

    def test_update_basic(self):
        self.client.login(username='chicommons', password='chicommons')
        instance = Coop.objects.get(pk=self.instance_id)
        before_model_count = Coop.objects.count()
        before_rec_updated_date = instance.rec_updated_date

        url = reverse('coop-detail', args=[self.instance_id])
        request = {
            "name":  "This is a new name",
            "enabled": False,
            "web_site": "http://google.com",
            "description": "This is a revised description",
            "approved": True,
            "proposed_changes": {"change1": "This is change 1", "change2": "This is change 2"},
            "reject_reason": "This is a reject reason.",
            "coop_public": False,
            "status": "This is a status",
            "scope": "This is a scope",
            "tags": "These are tags",
            "rec_source": "API Input",
            "rec_updated_by": 1,
            "rec_updated_date": "1996-03-31T18:30:00"
        }

        response = self.client.patch(url, request, format='json')

        try:
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(Coop.objects.count(), before_model_count)
            coop = Coop.objects.get(pk=self.instance_id)
            self.assertEqual(coop.name, request["name"])
            self.assertEqual(coop.enabled, request["enabled"])
            self.assertEqual(coop.web_site, request["web_site"])
            self.assertEqual(coop.description, request["description"])
            self.assertEqual(coop.approved, request["approved"])
            self.assertEqual(coop.proposed_changes, request["proposed_changes"])
            self.assertEqual(coop.coop_public, request["coop_public"])
            self.assertEqual(coop.status, request["status"])
            self.assertEqual(coop.scope, request["scope"])
            self.assertEqual(coop.tags, request["tags"])
            self.assertEqual(coop.rec_source, request["rec_source"])
            self.assertNotEqual(coop.rec_updated_by.id, request["rec_updated_by"])
            self.assertEqual(coop.rec_updated_by.id, self.modifying_user.id)
            self.assertNotEqual(coop.rec_updated_date, datetime.datetime.strptime( request["rec_updated_date"], "%Y-%m-%dT%H:%M:%S"))
            self.assertGreater(coop.rec_updated_date, before_rec_updated_date) 

            self.assertEqual(coop.contact_methods.count(), instance.contact_methods.count())
            self.assertEqual(coop.types.count(), instance.types.count())
            self.assertEqual(coop.people.count(), instance.people.count())
            self.assertEqual(coop.coop_address_tags.count(), instance.coop_address_tags.count())
        except:
            print(response.data)
            raise

    def test_update_with_empty_arrays(self):
        self.client.login(username='admin', password='admin')
        instance = Coop.objects.get(pk=self.instance_id)
        before_model_count = Coop.objects.count()

        url = reverse('coop-detail', args=[self.instance_id])
        request = {
            "contact_methods": [],
            "people": [],
            "coop_address_tags": [],
            "types": []
        }
        response = self.client.patch(url, request, format='json')

        try:
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(Coop.objects.count(), before_model_count)
            coop = Coop.objects.get(pk=self.instance_id)
            self.assertEqual(coop.types.count(), 0)
            self.assertEqual(coop.contact_methods.count(), 0)
            self.assertEqual(coop.people.count(), 0)
            self.assertEqual(coop.coop_address_tags.count(), 0)
        except:
            print(response.data)
            raise
    
    def test_update_with_loaded_arrays(self):
        self.client.login(username='admin', password='admin')
        instance = Coop.objects.get(pk=self.instance_id)
        before_model_count = Coop.objects.count()

        url = reverse('coop-detail', args=[self.instance_id])
        request = {
            "types": [ {"name": "Museum"}, {"name": "Swimming Pool"}],
            "contact_methods": [                
                { "type": "EMAIL", "is_public": True, "email": "myemail@example.com" },
                { "type": "PHONE", "is_public": True, "phone": "+17739441426"}       
            ],
            "people": [
                { "first_name": "Max", "last_name": "Adler", "is_public": False, "contact_methods": [] }, 
                { "first_name": "Jean Baptiste", "last_name": "Pointe DuSable", "is_public": False, "contact_methods": [
                    { "type": "EMAIL", "is_public": True, "email": "jbpd@example.com" },
                    { "type": "PHONE", "is_public": True, "phone": "+17735555555" },
                ] },
                { "first_name": "Abraham", "last_name": "Lincoln", "is_public": False, "contact_methods": [
                    { "type": "EMAIL", "is_public": True, "email": "abe@example.com" }
                ] }
            ],
            "coop_address_tags": [
                {
                    "is_public": True,
                    "address": {
                        "raw": "875 N Michigan Ave",
                        "formatted": "875 N Michigan Ave",
                        "locality": "Chicago",
                        "state": "IL",
                        "postal_code": "60611",
                        "country": "United States"
                    }
                },
                {
                    "is_public": True,
                    "address": {
                        "raw": "200 E Randolph St",
                        "formatted": "200 E Randolph St",
                        "locality": "Chicago",
                        "state": "IL",
                        "postal_code": "60601",
                        "country": "United States"
                    }
                }
            ],

        }
        response = self.client.patch(url, request, format='json')
        try:
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(Coop.objects.count(), before_model_count)

            coop = Coop.objects.get(pk=self.instance_id)
            self.assertEqual(coop.types.count(), 2)
            self.assertIn( request["types"][0]["name"], coop.types.values_list('name', flat=True))
            self.assertIn( request["types"][1]["name"], coop.types.values_list('name', flat=True))

            self.assertEqual(coop.contact_methods.count(), 2)
            self.assertIn( request["contact_methods"][0]["email"], coop.contact_methods.values_list('email', flat=True))
            self.assertIn( request["contact_methods"][1]["phone"], coop.contact_methods.values_list('phone', flat=True))

            self.assertEqual(coop.people.count(), 3)
            self.assertIn( request["people"][0]["first_name"], coop.people.values_list('first_name', flat=True))
            self.assertIn( request["people"][1]["first_name"], coop.people.values_list('first_name', flat=True))
            self.assertIn( request["people"][2]["first_name"], coop.people.values_list('first_name', flat=True))

            self.assertEqual(coop.coop_address_tags.count(), 2)
            self.assertIn( request["coop_address_tags"][0]["address"]["raw"], coop.coop_address_tags.values_list('address__raw', flat=True))
            self.assertIn( request["coop_address_tags"][1]["address"]["raw"], coop.coop_address_tags.values_list('address__raw', flat=True))
        except:
            print(response.data)
            raise

class PeopleCreateTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('create_countries')
        call_command('create_states')
    
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

class PeopleUpdateTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('create_countries')
        call_command('create_states')

    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', email='test@example.com', password='admin')
        #self.token = Token.objects.create(user=self.user)
        #self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key) 

        test_coop_1 = Coop.objects.create(
            name = "Test People Update 1",
            enabled = True,
            web_site = "http://example.com",
            description = "This is a description",
            approved = False,
            rec_updated_by = self.user
        )
        test_coop_1.save()
        self.test_coop_1_id = test_coop_1.id

        test_coop_2 = Coop.objects.create(
            name = "Test People Update 2",
            enabled = True,
            web_site = "http://example.com",
            description = "This is a description",
            approved = False,
            rec_updated_by = self.user
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

    def test_update_basic(self):
        self.client.login(username='admin', password='admin')
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
        self.client.login(username='admin', password='admin')
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
        self.client.login(username='admin', password='admin')
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
        self.client.login(username='admin', password='admin')
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
            # Validate that no instances were created
            self.assertEqual(Person.objects.count(), before_person_count)
            self.assertEqual(Coop.objects.count(), before_coop_count)
            self.assertEqual(ContactMethod.objects.count(), before_contactmethod_count)
        except:
            print(response.data)
            raise
    
    def test_update_with_coops(self):
        self.client.login(username='admin', password='admin')
        before_person_count = Person.objects.count()
        before_coop_count = Coop.objects.count()
        before_contactmethod_count = ContactMethod.objects.count()
        instance = Person.objects.get(pk=self.test_person_id)

        url = reverse('person-detail', args=[self.test_person_id])
        print("test_coop_2_id: %s" % self.test_coop_2_id)
        print("type test_coop_2_id: %s" % type(self.test_coop_2_id))
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

class AddressSerializerTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('create_countries')
        call_command('create_states')

    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', email='test@example.com', password='admin')
        #self.token = Token.objects.create(user=self.user)
        #self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key) 

    def test_address_serializer(self):
        address_data = {
            "raw": "222 W. Merchandise Mart Plaza, Suite 1212",
            "formatted": "222 W. Merchandise Mart Plaza, Suite 1212",
            "locality": "Chicago",
            "state": "IL",
            "postal_code": "60654",
            "country": "United States"
        }

        address_serializer = AddressSerializer(data=address_data)
        if address_serializer.is_valid():
            address = address_serializer.save()
        else: 
            raise

        self.assertEqual(Address.objects.count(), 1) 
        self.assertEqual(Locality.objects.count(), 1) 

        new_address = Address.objects.get(pk=address.id)
        self.assertEqual(new_address.raw, address_data["raw"]) 
        self.assertEqual(new_address.formatted, address_data["formatted"]) 
        self.assertEqual(new_address.locality.postal_code, address_data["postal_code"]) 
        self.assertEqual(new_address.locality.name, address_data["locality"]) 
        self.assertEqual(new_address.locality.state.code, address_data["state"]) 
        self.assertEqual(new_address.locality.state.country.name, address_data["country"]) 
    
    def test_address_serializer_without_optionals(self):
        address_data = {
            "raw": "222 W. Merchandise Mart Plaza, Suite 1212",
            "locality": "Chicago",
            "state": "IL",
            "postal_code": "60654"
        }

        address_serializer = AddressSerializer(data=address_data)
        if address_serializer.is_valid():
            address = address_serializer.save()
        else: 
            raise

        self.assertEqual(Address.objects.count(), 1) 
        self.assertEqual(Locality.objects.count(), 1) 

        new_address = Address.objects.get(pk=address.id)
        self.assertEqual(new_address.raw, address_data["raw"]) 
        self.assertEqual(new_address.formatted, "") 
        self.assertEqual(new_address.locality.postal_code, address_data["postal_code"]) 
        self.assertEqual(new_address.locality.name, address_data["locality"]) 
        self.assertEqual(new_address.locality.state.code, address_data["state"]) 
        self.assertEqual(new_address.locality.state.country.name, "United States")


class CoopAddressTagsSerializerTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('create_countries')
        call_command('create_states')

    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', email='test@example.com', password='admin')
        #self.token = Token.objects.create(user=self.user)
        #self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key) 

    def test_create(self):
        cat_data = {
            "is_public": True,
            "address": {
                "raw": "222 W. Merchandise Mart Plaza, Suite 1212",
                "formatted": "222 W. Merchandise Mart Plaza, Suite 1212",
                "locality": "Chicago",
                "state": "IL",
                "postal_code": "60654",
                "country": "United States"
            }
        }

        cat_serializer = CoopAddressTagsSerializer(data = cat_data)
        if cat_serializer.is_valid():
            cat = cat_serializer.save()
        else: 
            raise       

        self.assertEqual(CoopAddressTags.objects.count(), 1)
        self.assertEqual(Address.objects.count(), 1) 
        self.assertEqual(Locality.objects.count(), 1) 

        new_cat = CoopAddressTags.objects.get(pk=cat.id)
        self.assertEqual(new_cat.is_public, cat_data["is_public"])
        self.assertEqual(new_cat.address.raw, cat_data["address"]["raw"]) 
        self.assertEqual(new_cat.address.formatted, cat_data["address"]["formatted"]) 
        self.assertEqual(new_cat.address.locality.postal_code, cat_data["address"]["postal_code"]) 
        self.assertEqual(new_cat.address.locality.name, cat_data["address"]["locality"]) 
        self.assertEqual(new_cat.address.locality.state.code, cat_data["address"]["state"]) 
        self.assertEqual(new_cat.address.locality.state.country.name, cat_data["address"]["country"]) 

    def test_update(self):
        cat_create_data = {
            "is_public": False,
            "address": {
                "raw": "222 W. Merchandise Mart Plaza, Suite 1212",
                "formatted": "222 W. Merchandise Mart Plaza, Suite 1212",
                "locality": "Chicago",
                "state": "IL",
                "postal_code": "60654",
                "country": "United States"
            }
        }
        cat_serializer = CoopAddressTagsSerializer(data = cat_create_data)
        if cat_serializer.is_valid():
            cat = cat_serializer.save()
        else: 
            self.fail("Invalid CAT Creation")

        cat_update_data = {
            "is_public": True,
            "address": {
                "raw": "2800 N California Ave",
                "formatted": "2800 N California Ave",
                "locality": "Chicago",
                "state": "IL",
                "postal_code": "60618",
                "country": "United States"
            }
        }
        cat_serializer = CoopAddressTagsSerializer(cat, data=cat_update_data)
        if cat_serializer.is_valid():
            cat = cat_serializer.save()
        else: 
            self.fail("Invalid CAT Update")
        
        self.assertEqual(CoopAddressTags.objects.count(), 1)
        self.assertEqual(Address.objects.count(), 1) 
        self.assertEqual(Locality.objects.count(), 2) #Original locality from create will remain in addition to new locality from update

        new_cat = CoopAddressTags.objects.get(pk=cat.id)
        self.assertEqual(new_cat.is_public, cat_update_data["is_public"])
        #self.assertEqual(new_cat.address.raw, cat_update_data["address"]["raw"]) 
        self.assertEqual(new_cat.address.formatted, cat_update_data["address"]["formatted"]) 
        self.assertEqual(new_cat.address.locality.postal_code, cat_update_data["address"]["postal_code"]) 
        self.assertEqual(new_cat.address.locality.name, cat_update_data["address"]["locality"]) 
        self.assertEqual(new_cat.address.locality.state.code, cat_update_data["address"]["state"]) 
        self.assertEqual(new_cat.address.locality.state.country.name, cat_update_data["address"]["country"]) 