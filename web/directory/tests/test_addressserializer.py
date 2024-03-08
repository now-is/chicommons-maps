from directory.models import Address
from directory.serializers import AddressSerializer
from django.contrib.auth.models import User
from rest_framework.test import APITestCase

class TestAddressSerializer(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # call_command('create_countries')
        # call_command('create_states')
        pass

    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', email='test@example.com', password='admin')
        #self.token = Token.objects.create(user=self.user)
        #self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key) 

    def test_address_serializer(self):
        address_data = {
            "street_address": "222 W. Merchandise Mart Plaza, Suite 1212",
            "city": "Chicago",
            "state": "IL",
            "postal_code": "60654",
            "country": "US"
        }

        address_serializer = AddressSerializer(data=address_data)
        if address_serializer.is_valid():
            address = address_serializer.save()
        else: 
            raise

        self.assertEqual(Address.objects.count(), 1) 

        new_address = Address.objects.get(pk=address.id)
        self.assertEqual(new_address.street_address, address_data["street_address"]) 
        self.assertEqual(new_address.postal_code, address_data["postal_code"]) 
        self.assertEqual(new_address.city, address_data["city"]) 
        self.assertEqual(new_address.state, address_data["state"]) 
        self.assertEqual(new_address.country, address_data["country"]) 
    
    def test_address_serializer_without_optionals(self):
        address_data = {
            "street_address": "222 W. Merchandise Mart Plaza, Suite 1212",
            "city": "Chicago",
            "state": "IL",
            "postal_code": "60654"
        }

        address_serializer = AddressSerializer(data=address_data)
        if address_serializer.is_valid():
            address = address_serializer.save()
        else: 
            raise

        self.assertEqual(Address.objects.count(), 1) 

        new_address = Address.objects.get(pk=address.id)
        self.assertEqual(new_address.street_address, address_data["street_address"]) 
        self.assertEqual(new_address.postal_code, address_data["postal_code"]) 
        self.assertEqual(new_address.city, address_data["city"]) 
        self.assertEqual(new_address.state, address_data["state"]) 
        self.assertEqual(new_address.country, "US") 

