from directory.models import Coop
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
import json
import pathlib

def remove_keys_from_dict(obj, keys_to_remove):
    """
    Recursively remove specified keys from a dictionary, all its nested dictionaries,
    and any dictionaries within lists.
    """
    if isinstance(obj, dict):
        return {key: remove_keys_from_dict(value, keys_to_remove) 
                for key, value in obj.items() if key not in keys_to_remove}
    elif isinstance(obj, list):
        return [remove_keys_from_dict(item, keys_to_remove) for item in obj]
    else:
        return obj

class TestCoopList(APITestCase):
    @classmethod
    def setUpTestData(cls):
        pass
        
    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', email='test@example.com', password='admin')
        self.client.login(username='admin', password='admin')
        url = reverse('coop-list')
        coops = [
            {
                "name": "Test Coop 1 Apple",
                "types": [ {"name": "Library"} ],
                "enabled": True,
                "contact_methods": [
                    { "type": "EMAIL", "is_public": True, "email": "myemail@example.com" },
                    { "type": "PHONE", "is_public": True, "phone": "+17739441426" }          
                ],
                "web_site": "http://www.example.com/",
                "description": "My Coop Description",
                "approved": True,
                "proposed_changes": { "description": "Testing testing testing." },
                "reject_reason": "This is sample data.",
                "coop_public": False,
                "status": "Testing",
                "scope": "Testing",
                "tags": "tag1, tag2, tag3", 
                "rec_source": "Testing", 
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
                    {"first_name": "Steve", "last_name": "Smith", "is_public": False, 
                     "contact_methods": [
                            { "type": "EMAIL", "is_public": True, "email": "stevesmith@example.com" }
                        ],
                    }
                ]
            },
            {
                "name": "Test Coop 2 Banana",
                "types": [ {"name": "Museum"}, {"name": "Laboratory"} ],
                "enabled": True,
                "contact_methods": [
                    { "type": "EMAIL", "is_public": True, "email": "myemail@example2.com" },
                    { "type": "EMAIL", "is_public": True, "email": "hello@example2.com" },
                    { "type": "PHONE", "is_public": True, "phone": "+13122222222" }          
                ],
                "web_site": "http://www.example2.com/",
                "description": "My Coop Description",
                "approved": True,
                "proposed_changes": { "description": "Testing testing testing." },
                "reject_reason": "This is sample data.",
                "coop_public": False,
                "status": "Testing", 
                "scope": "Testing", 
                "tags": "tag1, tag2, tag3",
                "rec_source": "Testing",
                "coop_address_tags": [
                    {
                        "is_public": True,
                        "address": {
                            "street_address": "225 N Columbus Dr",
                            "city": "Chicago",
                            "state": "IL",
                            "postal_code": "60601",
                            "country": "US"
                        }
                    },
                    {
                        "is_public": True,
                        "address": {
                            "street_address": "400 N Michigan Ave",
                            "city": "Chicago",
                            "state": "IL",
                            "postal_code": "60611",
                            "country": "US"
                        }
                    }
                ],
                "people": [
                    {"first_name": "Cameron", "last_name": "Ellison", "is_public": False, "contact_methods": [
                        { "type": "EMAIL", "is_public": True, "email": "ellison@example2.com" },
                        { "type": "EMAIL", "is_public": True, "email": "ellison_spam@example2.com" }
                    ]}, 
                    {"first_name": "Harry", "last_name": "Underwood", "is_public": False, "contact_methods": [
                        { "type": "EMAIL", "is_public": True, "email": "underwood@example2.com" },
                        { "type": "PHONE", "is_public": True, "phone": "+13122222223" }
                    ]}
                ]
            },
            {
                "name": "Test Coop 3 Apple",
                "types": [ {"name": "Museum"} ],
                "enabled": True,
                "contact_methods": [ 
                ],
                "web_site": "http://www.example3.com/",
                "description": "My Coop Description",
                "approved": True,
                "proposed_changes": { "description": "Testing testing testing." },
                "reject_reason": "This is sample data.",
                "coop_public": False,
                "status": "Testing", 
                "scope": "Testing", 
                "tags": "tag1, tag2, tag3",
                "rec_source": "Testing",
                "coop_address_tags": [
                    {
                        "is_public": True,
                        "address": {
                            "street_address": "300 E Ontario St",
                            "city": "Chicago",
                            "state": "IL",
                            "postal_code": "60611",
                            "country": "US"
                        }
                    }
                ],
                "people": []
            },            
            {
                "name": "Test Coop 4 Banana",
                "types": [ {"name": "Arboretum"} ],
                "enabled": True,
                "contact_methods": [ 
                ],
                "web_site": "http://www.example4.com/",
                "description": "My Coop Description",
                "approved": True,
                "proposed_changes": { "description": "Testing testing testing." },
                "reject_reason": "This is sample data.",
                "coop_public": False,
                "status": "Testing", 
                "scope": "Testing", 
                "tags": "tag1, tag2, tag3",
                "rec_source": "Testing",
                "coop_address_tags": [
                    {
                        "is_public": True,
                        "address": {
                            "street_address": "400 N State St",
                            "city": "Chicago",
                            "state": "IL",
                            "postal_code": "60654",
                            "country": "US"
                        }
                    }
                ],
                "people": []
            },
            {
                "name": "Test Coop 5 Apple",
                "types": [ {"name": "Arboretum"} ],
                "enabled": True,
                "contact_methods": [ 
                ],
                "web_site": "http://www.example5.com/",
                "description": "My Coop Description",
                "approved": True,
                "proposed_changes": { "description": "Testing testing testing." },
                "reject_reason": "This is sample data.",
                "coop_public": False,
                "status": "Testing", 
                "scope": "Testing", 
                "tags": "tag1, tag2, tag3",
                "rec_source": "Testing",
                "coop_address_tags": [
                    {
                        "is_public": True,
                        "address": {
                            "street_address": "2200 Main St",
                            "city": "Evanston",
                            "state": "IL",
                            "postal_code": "60202",
                            "country": "US"
                        }
                    }
                ],
                "people": []
            },
            {
                "name": "Test Coop 6 Banana",
                "types": [ {"name": "Arboretum"} ],
                "enabled": True,
                "contact_methods": [ 
                ],
                "web_site": "http://www.example6.com/",
                "description": "My Coop Description",
                "approved": True,
                "proposed_changes": { "description": "Testing testing testing." },
                "reject_reason": "This is sample data.",
                "coop_public": False,
                "status": "Testing", 
                "scope": "Testing", 
                "tags": "tag1, tag2, tag3",
                "rec_source": "Testing",
                "coop_address_tags": [
                    {
                        "is_public": True,
                        "address": {
                            "street_address": "800 Michigan Ave",
                            "city": "Evanston",
                            "state": "IL",
                            "postal_code": "60202",
                            "country": "US"
                        }
                    }
                ],
                "people": []
            },

        ]

        for request in coops:
            response = self.client.post(url, request, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_list_all(self):
        results_filename = "TestCoopList_test_list_all.json"
        results_path = pathlib.Path(__file__).parent / 'result_files' / results_filename
        results_path.resolve()

        url = reverse('coop-list')
        request = {}
        response = self.client.get(url, data=request, format='json')
        modified_data = remove_keys_from_dict(response.json(), ['rec_updated_date', 'id']) # responses should be identical except for rec_updated_date (depends on time it is run), and id (depends on order of tests). Removes those keys to streamline response comparisons.
        response_data = json.dumps(modified_data, indent=4, sort_keys=True)

        with open(results_path, 'w') as file:
            file.write(response_data)

        with open(results_path, "r") as file:
            expected_data = file.read()

        self.maxDiff = None
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Coop.objects.count(), 6) 
        self.assertEqual(response_data, expected_data)
    
    def test_filter_name(self):
        results_filename = "TestCoopList_test_filter_name.json"
        results_path = pathlib.Path(__file__).parent / 'result_files' / results_filename
        results_path.resolve()
        
        url = reverse('coop-list')
        request = {
            'name': 'banana'
        }
        response = self.client.get(url, data=request, format='json')
        modified_data = remove_keys_from_dict(response.json(), ['rec_updated_date', 'id']) # responses should be identical except for rec_updated_date (depends on time it is run), and id (depends on order of tests). Removes those keys to streamline response comparisons.
        response_data = json.dumps(modified_data, indent=4, sort_keys=True)

        with open(results_path, 'w') as file:
            file.write(response_data)

        with open(results_path, "r") as file:
            expected_data = file.read()

        self.maxDiff = None
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Coop.objects.count(), 6)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response_data, expected_data)        
    
    def test_filter_street(self):
        results_filename = "TestCoopList_test_filter_street.json"
        results_path = pathlib.Path(__file__).parent / 'result_files' / results_filename
        results_path.resolve()

        url = reverse('coop-list')
        request = {
            'street': 'michigan'
        }
        response = self.client.get(url, data=request, format='json')
        modified_data = remove_keys_from_dict(response.json(), ['rec_updated_date', 'id']) # responses should be identical except for rec_updated_date (depends on time it is run), and id (depends on order of tests). Removes those keys to streamline response comparisons.
        response_data = json.dumps(modified_data, indent=4, sort_keys=True)

        with open(results_path, 'w') as file:
            file.write(response_data)

        with open(results_path, "r") as file:
            expected_data = file.read()

        self.maxDiff = None
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Coop.objects.count(), 6)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response_data, expected_data)
    
    def test_filter_city(self):
        results_filename = "TestCoopList_test_filter_city.json"
        results_path = pathlib.Path(__file__).parent / 'result_files' / results_filename
        results_path.resolve()

        url = reverse('coop-list')
        request = {
            'city': 'Chicago'
        }
        response = self.client.get(url, data=request, format='json')
        modified_data = remove_keys_from_dict(response.json(), ['rec_updated_date', 'id']) # responses should be identical except for rec_updated_date (depends on time it is run), and id (depends on order of tests). Removes those keys to streamline response comparisons.
        response_data = json.dumps(modified_data, indent=4, sort_keys=True)

        with open(results_path, 'w') as file:
            file.write(response_data)

        with open(results_path, "r") as file:
            expected_data = file.read()

        self.maxDiff = None
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Coop.objects.count(), 6)
        self.assertEqual(len(response.data), 4)
        self.assertEqual(response_data, expected_data)  
    
    def test_filter_zip(self):
        results_filename = "TestCoopList_test_filter_zip.json"
        results_path = pathlib.Path(__file__).parent / 'result_files' / results_filename
        results_path.resolve()

        url = reverse('coop-list')
        request = {
            'zip': '60611'
        }
        response = self.client.get(url, data=request, format='json')
        modified_data = remove_keys_from_dict(response.json(), ['rec_updated_date', 'id']) # responses should be identical except for rec_updated_date (depends on time it is run), and id (depends on order of tests). Removes those keys to streamline response comparisons.
        response_data = json.dumps(modified_data, indent=4, sort_keys=True)

        with open(results_path, 'w') as file:
            file.write(response_data)

        with open(results_path, "r") as file:
            expected_data = file.read()

        self.maxDiff = None
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Coop.objects.count(), 6)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response_data, expected_data) 

    def test_filter_types(self):
        results_filename = "TestCoopList_test_filter_types.json"
        results_path = pathlib.Path(__file__).parent / 'result_files' / results_filename
        results_path.resolve()

        url = reverse('coop-list')
        request = {
            'types': 'Library,Laboratory,Arboretum'
        }
        response = self.client.get(url, data=request, format='json')
        modified_data = remove_keys_from_dict(response.json(), ['rec_updated_date', 'id']) # responses should be identical except for rec_updated_date (depends on time it is run), and id (depends on order of tests). Removes those keys to streamline response comparisons.
        response_data = json.dumps(modified_data, indent=4, sort_keys=True)

        with open(results_path, 'w') as file:
            file.write(response_data)

        with open(results_path, "r") as file:
            expected_data = file.read()

        self.maxDiff = None
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Coop.objects.count(), 6)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response_data, expected_data) 
    
    def test_filter_stacked(self):
        results_filename = "TestCoopList_test_filter_stacked.json"
        results_path = pathlib.Path(__file__).parent / 'result_files' / results_filename
        results_path.resolve()

        url = reverse('coop-list')
        request = {
            # find #2
            'types': 'Library,Laboratory,Arboretum', #returns 1,2,4,5,6
            'city': 'chicago', #returns 1,2,3,4
            'name': 'banana', #returns 2,4,6
            'street': 'michigan', #returns 2,6
            'zip': '60611', #returns 2,3

        }
        response = self.client.get(url, data=request, format='json')
        modified_data = remove_keys_from_dict(response.json(), ['rec_updated_date', 'id']) # responses should be identical except for rec_updated_date (depends on time it is run), and id (depends on order of tests). Removes those keys to streamline response comparisons.
        response_data = json.dumps(modified_data, indent=4, sort_keys=True)

        with open(results_path, 'w') as file:
            file.write(response_data)

        with open(results_path, "r") as file:
            expected_data = file.read()

        self.maxDiff = None
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Coop.objects.count(), 6)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response_data, expected_data) 