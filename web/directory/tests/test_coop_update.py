from directory.models import Coop, CoopType, ContactMethod, Person, CoopAddressTags
from directory.serializers import AddressSerializer
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
import datetime

class TestCoopUpdate(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # call_command('create_countries')
        # call_command('create_states')
        pass

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
            "street_address": "233 S Wacker Dr",
            "city": "Chicago",
            "state": "IL",
            "postal_code": "60606",
            "country": "US"
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
                        "street_address": "875 N Michigan Ave",
                        "city": "Chicago",
                        "state": "IL",
                        "postal_code": "60611",
                        "country": "US"
                    }
                },
                {
                    "is_public": True,
                    "address": {
                        "street_address": "200 E Randolph St",
                        "city": "Chicago",
                        "state": "IL",
                        "postal_code": "60601",
                        "country": "US"
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
            self.assertIn( request["coop_address_tags"][0]["address"]["street_address"], coop.coop_address_tags.values_list('address__street_address', flat=True))
            self.assertIn( request["coop_address_tags"][1]["address"]["street_address"], coop.coop_address_tags.values_list('address__street_address', flat=True))
        except:
            print(response.data)
            raise
