from directory.models import CoopProposal, CoopPublic, CoopX, CoopType, ContactMethod, PersonX, CoopAddressTags, Address, CoopAddressTagsX
from directory.serializers import CoopProposalToCreateSerializer, CoopProposalReviewSerializer, CoopProposalToUpdateSerializer, CoopProposalToDeleteSerializer, NewCoopProposalSerializer
from rest_framework.test import APITestCase
import json
from unittest.mock import patch, MagicMock
from directory.services.location_service import LocationService
from ratelimit import limits, RateLimitException
import datetime
from django.core.serializers import serialize
import pathlib
from . import helpers

class TestCoopX(APITestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):
        self.staging_dir_path = (pathlib.Path(__file__).parent / 'files' / 'staging').resolve()
        self.testcases_dir_path = (pathlib.Path(__file__).parent / 'files' / 'testcases').resolve()
        self.create_data = {
            "operation": "CREATE",
            "coop": {
                "name": "Test Max 9999",
                "web_site": "http://www.1871.com/",
                "description": "My Coop Description",
                "is_public": True, # TODO - Confirm biz logic. Should you be able to approve the Coop create in the same call you create it?
                "scope": "Testing", #TODO - What are acceptable values?
                "tags": "tag1, tag2, tag3", #TODO - What are acceptable values?
                "types": [ {"name": "Library"}, {"name": "Museum"} ],
                "contact_methods": [
                    { "type": "EMAIL", "is_public": True, "email": "myemail@example.com" },
                    { "type": "PHONE", "is_public": True, "phone": "+17739441426" }          
                ],
                "people": [
                    {"first_name": "John", "last_name": "Doe", "is_public": False, "contact_methods": []}, 
                    {"first_name": "Steve", "last_name": "Smith", "is_public": False, "contact_methods": [
                        { "type": "EMAIL", "is_public": True, "email": "stevesmith@example.com" },
                        { "type": "PHONE", "is_public": True, "phone": "+13125555555" }
                    ]}
                ],
                "addresses": [
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
                            "street_address": "400 W 76th Street",
                            "city": "Chicago",
                            "state": "IL",
                            "postal_code": "60620",
                            "country": "US"
                        }
                    }
                ]
            }
        }
        self.update_data = {
            "operation": "UPDATE",
            "coop_public_id": None,
            "coop": {
                "name": "Test Max 8888",
                "web_site": "http://www.example.com/",
                "description": "Testing",
                "is_public": True, # TODO - Confirm biz logic. Should you be able to approve the Coop create in the same call you create it?
                "scope": "Testing Testing", #TODO - What are acceptable values?
                "tags": "tag1, tag2, tag3, tag4", #TODO - What are acceptable values?
                "types": [ {"name": "Aquarium"}, {"name": "Park"}, {"name": "Arboretum"} ],
                "contact_methods": [
                    { "type": "EMAIL", "is_public": True, "email": "myemail2@example.com" },
                    { "type": "PHONE", "is_public": True, "phone": "+17739441427" },
                    { "type": "EMAIL", "is_public": True, "email": "myemail3@example.com" },
                    { "type": "PHONE", "is_public": True, "phone": "+17739441428" }
                ],
                "people": [
                    {"first_name": "Debra", "last_name": "Silverstein", "is_public": False, "contact_methods": []}, 
                    {"first_name": "Maria", "last_name": "Hadden", "is_public": False, "contact_methods": [
                        { "type": "PHONE", "is_public": True, "phone": "+13125555551" }
                    ]}, 
                    {"first_name": "Matt", "last_name": "Martin", "is_public": False, "contact_methods": [
                        { "type": "EMAIL", "is_public": True, "email": "example3@example.com" }
                    ]}, 
                    {"first_name": "Leni", "last_name": "Manna-Hoppenworth", "is_public": False, "contact_methods": [
                        { "type": "EMAIL", "is_public": True, "email": "example4@example.com" },
                        { "type": "PHONE", "is_public": True, "phone": "+13125555552" }
                    ]}
                ],
                "addresses": [
                    {
                        "is_public": True,
                        "address": {
                            "street_address": "1345 W 19th Street",
                            "city": "Chicago",
                            "state": "IL",
                            "postal_code": "60608",
                            "country": "US"
                        }
                    },                    
                    {
                        "is_public": True,
                        "address": {
                            "street_address": "3500 S Lake Park Ave",
                            "city": "Chicago",
                            "state": "IL",
                            "postal_code": "60653",
                            "country": "US"
                        }
                    },
                    {
                        "is_public": True,
                        "address": {
                            "street_address": "6500 S Pulaski Rd",
                            "city": "Chicago",
                            "state": "IL",
                            "postal_code": "60629",
                            "country": "US"
                        }
                    }
                ]
            }
        }
        self.delete_data = {
            "operation": "DELETE",
            "coop_public_id": None
        }
        self.approval_data = {
            'id': None,
            'proposal_status': "APPROVED",
            'review_notes': "lgtm"
        }
        self.mock_raw_dict = {'lat': 37.4221, 'lon': -122.0841, 'place_id': 'XXXYYYYZZZ', 'address': {'county': 'Testing County'}}
  
    @patch('directory.services.location_service.Nominatim')
    def test_NewCoopProposalSerializer(self, mock_nominatim):
        # Setup mock response for Location Service's Geocode API (Nominatim)
        mock_nominatim.return_value.geocode.return_value.configure_mock(raw=self.mock_raw_dict)

        create_data = self.create_data

        coop_proposal_to_create_serializer = NewCoopProposalSerializer(data=create_data)
        if coop_proposal_to_create_serializer.is_valid():
            coop_proposal = coop_proposal_to_create_serializer.save()
        else: 
            self.fail(coop_proposal_to_create_serializer.errors)

        self.assertEqual(CoopProposal.objects.count(), 1)
        self.assertEqual(CoopPublic.objects.count(), 0)
        self.assertEqual(CoopX.objects.count(), 1)
        self.assertEqual(CoopType.objects.count(), 2)
        self.assertEqual(ContactMethod.objects.count(), 4)
        self.assertEqual(PersonX.objects.count(), 2)
        self.assertEqual(CoopAddressTagsX.objects.count(), 2)
        self.assertEqual(Address.objects.count(), 2)

        # Validate CoopProposal
        self.assertEqual(CoopProposal.objects.filter(proposal_status="PENDING").count(), 1)
        self.assertEqual(CoopProposal.objects.filter(proposal_status="APPROVED").count(), 0)
        self.assertEqual(CoopProposal.objects.filter(proposal_status="REJECTED").count(), 0)

        self.assertEqual(coop_proposal.operation, "CREATE")
        self.assertEqual(coop_proposal.proposal_status, "PENDING")
        self.assertIsNone(coop_proposal.coop_public)

        # Validate CoopPublic
        self.assertEqual(CoopPublic.objects.filter(status="ACTIVE").count(), 0)
        self.assertEqual(CoopPublic.objects.filter(status="REMOVED").count(), 0)

        # Validate CoopX
        self.assertEqual(CoopX.objects.filter(status="ACTIVE").count(), 0)
        self.assertEqual(CoopX.objects.filter(status="PROPOSAL").count(), 1)
        self.assertEqual(CoopX.objects.filter(status="ARCHIVED").count(), 0)

        coop = coop_proposal.coop
        self.assertEqual(coop.status, "PROPOSAL")
        self.assertEqual(coop.name, create_data["coop"]["name"])
        self.assertEqual(coop.web_site, create_data["coop"]["web_site"])
        self.assertEqual(coop.description, create_data["coop"]["description"])
        self.assertEqual(coop.is_public, create_data["coop"]["is_public"])
        self.assertEqual(coop.scope, create_data["coop"]["scope"])
        self.assertEqual(coop.tags, create_data["coop"]["tags"])

        coop_types = coop_proposal.coop.types.all()
        self.assertEqual(len(coop_types), 2)
        self.assertEqual(coop_types[0].name, create_data["coop"]["types"][0]["name"])
        self.assertEqual(coop_types[1].name, create_data["coop"]["types"][1]["name"])

        contact_methods = coop_proposal.coop.contact_methods.all()
        self.assertEqual(len(contact_methods), 2)
        self.assertEqual(contact_methods[0].email, create_data["coop"]["contact_methods"][0]["email"])
        self.assertEqual(contact_methods[0].phone, None)
        self.assertEqual(contact_methods[1].email, None)
        self.assertEqual(contact_methods[1].phone, create_data["coop"]["contact_methods"][1]["phone"])

        people = coop_proposal.coop.people.all()
        self.assertEqual(len(people), len(create_data["coop"]["people"]))
        for i in range(len(create_data["coop"]["people"])):
            self.assertEqual(people[i].first_name, create_data["coop"]["people"][i]["first_name"])
            self.assertEqual(people[i].last_name, create_data["coop"]["people"][i]["last_name"])
            people_contactmethods = people[i].contact_methods.all()
            for j in range(len(create_data["coop"]["people"][i]["contact_methods"])):
                if create_data["coop"]["people"][i]["contact_methods"][j]["type"]=="EMAIL":
                    self.assertEqual(people_contactmethods[j].email, create_data["coop"]["people"][i]["contact_methods"][j]["email"])
                if create_data["coop"]["people"][i]["contact_methods"][j]["type"]=="PHONE":
                    self.assertEqual(people_contactmethods[j].phone, create_data["coop"]["people"][i]["contact_methods"][j]["phone"])

        addresses = coop_proposal.coop.addresses.all()
        self.assertEqual(len(addresses), len(create_data["coop"]["addresses"]))
        for i in range(len(create_data["coop"]["addresses"])):
            self.assertEqual(addresses[i].address.street_address, create_data["coop"]["addresses"][i]["address"]["street_address"])
            self.assertEqual(addresses[i].address.city, create_data["coop"]["addresses"][i]["address"]["city"])
            self.assertEqual(addresses[i].address.state, create_data["coop"]["addresses"][i]["address"]["state"])
            self.assertEqual(addresses[i].address.postal_code, create_data["coop"]["addresses"][i]["address"]["postal_code"])
            self.assertEqual(addresses[i].address.country, create_data["coop"]["addresses"][i]["address"]["country"])

        # # When the structure of the result or test dataset changes, uncomment this
        # #    section and run to update results files. Recomment when running test cases. 
        # results_filename = "TestCoopX1.json"
        # results_filepath = (self.testcases_dir_path / results_filename).resolve()
        # results_data = [
        #     serialize('python', CoopProposal.objects.all()),
        #     serialize('python', CoopX.objects.all()),
        #     serialize('python', CoopPublic.objects.all())
        # ]
        # results_data = helpers.sanitize(results_data)

        # with open(results_filepath, 'w') as file:
        #     file.write(str(results_data))

        # print( results_data )
        # print("------")
            
        print( serialize('json', CoopProposal.objects.all()) )
        print( serialize('json', CoopX.objects.all()) )
        print( serialize('json', CoopPublic.objects.all()) )
        print("------")


        # ==============================
        #   Review proposal
        # ==============================
        approval_data = {
            'id': coop_proposal.id,
            'proposal_status': "APPROVED",
            'review_notes': "lgtm"
        }
        review_serializer = CoopProposalReviewSerializer(coop_proposal, data=approval_data)
        if review_serializer.is_valid():
            coop_proposal = review_serializer.save()
        else: 
            self.fail(review_serializer.errors)

        self.assertEqual(CoopProposal.objects.count(), 1)
        self.assertEqual(CoopPublic.objects.count(), 1)
        self.assertEqual(CoopX.objects.count(), 1)
        self.assertEqual(CoopType.objects.count(), 2)
        self.assertEqual(ContactMethod.objects.count(), 4)
        self.assertEqual(PersonX.objects.count(), 2)
        self.assertEqual(CoopAddressTagsX.objects.count(), 2)
        self.assertEqual(Address.objects.count(), 2)

        # Validate CoopProposal
        self.assertEqual(CoopProposal.objects.filter(proposal_status="PENDING").count(), 0)
        self.assertEqual(CoopProposal.objects.filter(proposal_status="APPROVED").count(), 1)
        self.assertEqual(CoopProposal.objects.filter(proposal_status="REJECTED").count(), 0)
        self.assertEqual(coop_proposal.operation, "CREATE")
        self.assertEqual(coop_proposal.proposal_status, approval_data["proposal_status"])
        self.assertEqual(coop_proposal.review_notes, approval_data["review_notes"])
        self.assertEqual(coop_proposal.coop_public.id, coop_proposal.coop_public.id)       

        # Validate CoopX
        self.assertEqual(CoopX.objects.filter(status="ACTIVE").count(), 1)
        self.assertEqual(CoopX.objects.filter(status="PROPOSAL").count(), 0)
        self.assertEqual(CoopX.objects.filter(status="ARCHIVED").count(), 0)
        active_coop = CoopX.objects.get(status="ACTIVE", coop_public_id=coop_proposal.coop_public.id)
        self.assertEqual(active_coop.status, "ACTIVE")
        self.assertEqual(active_coop.coop_public.id, coop_proposal.coop_public.id)

        # Validate CoopPublic
        self.assertEqual(CoopPublic.objects.filter(status="ACTIVE").count(), 1)
        self.assertEqual(CoopPublic.objects.filter(status="REMOVED").count(), 0)
        coop_public = coop_proposal.coop_public
        self.assertEqual(coop_public.status, "ACTIVE")

        print( serialize('json', CoopProposal.objects.all()) )
        print( serialize('json', CoopX.objects.all()) )
        print( serialize('json', CoopPublic.objects.all()) )
        print("------")

        # ==============================
        #   Create proposal to Update
        # ==============================

        update_data = self.update_data
        update_data["coop_public_id"] = coop_proposal.coop_public.id

        coop_proposal_to_update_serializer = NewCoopProposalSerializer(data=update_data)
        if coop_proposal_to_update_serializer.is_valid():
            coop_proposal = coop_proposal_to_update_serializer.save()
        else: 
            self.fail(coop_proposal_to_update_serializer.errors)

        self.assertEqual(CoopProposal.objects.count(), 2)
        self.assertEqual(CoopPublic.objects.count(), 1)
        self.assertEqual(CoopX.objects.count(), 2)
        self.assertEqual(CoopType.objects.count(), 5)
        self.assertEqual(ContactMethod.objects.count(), 12)
        self.assertEqual(PersonX.objects.count(), 6)
        self.assertEqual(CoopAddressTagsX.objects.count(), 5)
        self.assertEqual(Address.objects.count(), 5)

        # Validate CoopProposal
        self.assertEqual(CoopProposal.objects.filter(proposal_status="PENDING").count(), 1)
        self.assertEqual(CoopProposal.objects.filter(proposal_status="APPROVED").count(), 1)
        self.assertEqual(CoopProposal.objects.filter(proposal_status="REJECTED").count(), 0)

        self.assertEqual(coop_proposal.operation, "UPDATE")
        self.assertEqual(coop_proposal.proposal_status, "PENDING")
        self.assertIsNotNone(coop_proposal.coop_public)

        # Validate CoopPublic
        self.assertEqual(CoopPublic.objects.filter(status="ACTIVE").count(), 1)
        self.assertEqual(CoopPublic.objects.filter(status="REMOVED").count(), 0)
        coop_public = coop_proposal.coop_public
        self.assertEqual(coop_public.status, "ACTIVE")

        # Validate CoopX
        self.assertEqual(CoopX.objects.filter(status="ACTIVE").count(), 1)
        self.assertEqual(CoopX.objects.filter(status="PROPOSAL").count(), 1)
        self.assertEqual(CoopX.objects.filter(status="ARCHIVED").count(), 0)
        coop = coop_proposal.coop
        self.assertEqual(coop.status, "PROPOSAL")
        self.assertEqual(coop.coop_public.id, coop_proposal.coop_public.id)

        self.assertEqual(coop.name, update_data["coop"]["name"])
        self.assertEqual(coop.web_site, update_data["coop"]["web_site"])
        self.assertEqual(coop.description, update_data["coop"]["description"])
        self.assertEqual(coop.is_public, update_data["coop"]["is_public"])
        self.assertEqual(coop.scope, update_data["coop"]["scope"])
        self.assertEqual(coop.tags, update_data["coop"]["tags"])

        coop_types = coop.types.all()
        self.assertEqual(len(coop_types), 3)
        self.assertEqual(coop_types[0].name, update_data["coop"]["types"][0]["name"])
        self.assertEqual(coop_types[1].name, update_data["coop"]["types"][1]["name"])
        self.assertEqual(coop_types[2].name, update_data["coop"]["types"][2]["name"])

        contact_methods = coop.contact_methods.all()
        self.assertEqual(len(contact_methods), 4)
        self.assertEqual(contact_methods[0].email, update_data["coop"]["contact_methods"][0]["email"])
        self.assertEqual(contact_methods[0].phone, None)
        self.assertEqual(contact_methods[1].email, None)
        self.assertEqual(contact_methods[1].phone, update_data["coop"]["contact_methods"][1]["phone"])
        self.assertEqual(contact_methods[2].email, update_data["coop"]["contact_methods"][2]["email"])
        self.assertEqual(contact_methods[2].phone, None)
        self.assertEqual(contact_methods[3].email, None)
        self.assertEqual(contact_methods[3].phone, update_data["coop"]["contact_methods"][3]["phone"])

        people = coop.people.all()
        self.assertEqual(len(people), len(update_data["coop"]["people"]))
        for i in range(len(update_data["coop"]["people"])):
            self.assertEqual(people[i].first_name, update_data["coop"]["people"][i]["first_name"])
            self.assertEqual(people[i].last_name, update_data["coop"]["people"][i]["last_name"])
            people_contactmethods = people[i].contact_methods.all()
            for j in range(len(update_data["coop"]["people"][i]["contact_methods"])):
                if update_data["coop"]["people"][i]["contact_methods"][j]["type"]=="EMAIL":
                    self.assertEqual(people_contactmethods[j].email, update_data["coop"]["people"][i]["contact_methods"][j]["email"])
                if update_data["coop"]["people"][i]["contact_methods"][j]["type"]=="PHONE":
                    self.assertEqual(people_contactmethods[j].phone, update_data["coop"]["people"][i]["contact_methods"][j]["phone"])
        
        addresses = coop.addresses.all()
        self.assertEqual(len(addresses), len(update_data["coop"]["addresses"]))
        for i in range(len(update_data["coop"]["addresses"])):
            self.assertEqual(addresses[i].address.street_address, update_data["coop"]["addresses"][i]["address"]["street_address"])
            self.assertEqual(addresses[i].address.city, update_data["coop"]["addresses"][i]["address"]["city"])
            self.assertEqual(addresses[i].address.state, update_data["coop"]["addresses"][i]["address"]["state"])
            self.assertEqual(addresses[i].address.postal_code, update_data["coop"]["addresses"][i]["address"]["postal_code"])
            self.assertEqual(addresses[i].address.country, update_data["coop"]["addresses"][i]["address"]["country"])

        active_coop = CoopX.objects.get(status="ACTIVE", coop_public_id=coop_proposal.coop_public.id)
        self.assertEqual(active_coop.status, "ACTIVE")
        self.assertIsNotNone(active_coop.coop_public)
        self.assertEqual(active_coop.coop_public.id, 1)
        self.assertEqual(active_coop.coop_public, coop_proposal.coop_public)

        print( serialize('json', CoopProposal.objects.all()) )
        print( serialize('json', CoopX.objects.all()) )
        print( serialize('json', CoopPublic.objects.all()) )
        print("------")

        # ==============================
        #   Review proposal
        # ==============================
        approval_data = self.approval_data
        approval_data["id"] = coop_proposal.id

        review_serializer = CoopProposalReviewSerializer(coop_proposal, data=approval_data)
        if review_serializer.is_valid():
            coop_proposal = review_serializer.save()
        else: 
            self.fail(review_serializer.errors)

        self.assertEqual(CoopProposal.objects.count(), 2)
        self.assertEqual(CoopPublic.objects.count(), 1)
        self.assertEqual(CoopX.objects.count(), 2)
        self.assertEqual(CoopType.objects.count(), 5)
        self.assertEqual(ContactMethod.objects.count(), 12)
        self.assertEqual(PersonX.objects.count(), 6)
        self.assertEqual(CoopAddressTagsX.objects.count(), 5)
        self.assertEqual(Address.objects.count(), 5)

        print( serialize('json', CoopProposal.objects.all()) )

        self.assertEqual(CoopProposal.objects.filter(proposal_status="PENDING").count(), 0)
        self.assertEqual(CoopProposal.objects.filter(proposal_status="APPROVED").count(), 2)
        self.assertEqual(CoopProposal.objects.filter(proposal_status="REJECTED").count(), 0)

        self.assertEqual(CoopX.objects.filter(status="ACTIVE").count(), 1)
        self.assertEqual(CoopX.objects.filter(status="PROPOSAL").count(), 0)
        self.assertEqual(CoopX.objects.filter(status="ARCHIVED").count(), 1)

        self.assertEqual(CoopPublic.objects.filter(status="ACTIVE").count(), 1)
        self.assertEqual(CoopPublic.objects.filter(status="REMOVED").count(), 0)

        coop = coop_proposal.coop
        self.assertEqual(coop.coop_public.id, 1)
        self.assertEqual(coop.status, "ACTIVE")
        self.assertIsNotNone(coop.coop_public)
        self.assertEqual(coop.coop_public, coop_proposal.coop_public)

        archived_coop = CoopX.objects.get(status="ARCHIVED", coop_public_id=coop_proposal.coop_public.id)
        self.assertEqual(archived_coop.status, "ARCHIVED")
        self.assertEqual(archived_coop.coop_public.id, 1)
        self.assertEqual(archived_coop.coop_public, coop_proposal.coop_public)

        coop_public = coop_proposal.coop_public
        self.assertEqual(coop_public.status, "ACTIVE")

        print( serialize('json', CoopProposal.objects.all()) )
        print( serialize('json', CoopX.objects.all()) )
        print( serialize('json', CoopPublic.objects.all()) )
        print("------")

        # ==============================
        #   Create proposal to Delete
        # ==============================
        delete_data = self.delete_data
        delete_data["coop_public_id"] = coop_proposal.coop_public.id

        coop_proposal_to_delete_serializer = NewCoopProposalSerializer(data=delete_data)
        if coop_proposal_to_delete_serializer.is_valid():
            coop_proposal = coop_proposal_to_delete_serializer.save()
        else: 
            self.fail(coop_proposal_to_delete_serializer.errors)

        self.assertEqual(CoopProposal.objects.count(), 3)
        self.assertEqual(CoopPublic.objects.count(), 1)
        self.assertEqual(CoopX.objects.count(), 2)
        self.assertEqual(CoopType.objects.count(), 5)
        self.assertEqual(ContactMethod.objects.count(), 12)
        self.assertEqual(PersonX.objects.count(), 6)
        self.assertEqual(CoopAddressTagsX.objects.count(), 5)
        self.assertEqual(Address.objects.count(), 5)

        self.assertEqual(CoopProposal.objects.filter(proposal_status="PENDING").count(), 1)
        self.assertEqual(CoopProposal.objects.filter(proposal_status="APPROVED").count(), 2)
        self.assertEqual(CoopProposal.objects.filter(proposal_status="REJECTED").count(), 0)

        self.assertEqual(CoopX.objects.filter(status="ACTIVE").count(), 1)
        self.assertEqual(CoopX.objects.filter(status="PROPOSAL").count(), 0)
        self.assertEqual(CoopX.objects.filter(status="ARCHIVED").count(), 1)

        self.assertEqual(CoopPublic.objects.filter(status="ACTIVE").count(), 1)
        self.assertEqual(CoopPublic.objects.filter(status="REMOVED").count(), 0)

        self.assertEqual(coop_proposal.operation, "DELETE")

        coop_public = coop_proposal.coop_public
        self.assertEqual(coop_public.status, "ACTIVE")

        active_coop = CoopX.objects.get(status="ACTIVE", coop_public_id=coop_proposal.coop_public.id)
        self.assertEqual(active_coop.status, "ACTIVE")
        self.assertIsNotNone(active_coop.coop_public)
        self.assertEqual(active_coop.coop_public.id, 1)
        self.assertEqual(active_coop.coop_public, coop_proposal.coop_public)

        print( serialize('json', CoopProposal.objects.all()) )
        print( serialize('json', CoopX.objects.all()) )
        print( serialize('json', CoopPublic.objects.all()) )
        print("------")

        # ==============================
        #   Review proposal
        # ==============================
        approval_data = self.approval_data
        approval_data["id"] = coop_proposal.id

        review_serializer = CoopProposalReviewSerializer(coop_proposal, data=approval_data)
        if review_serializer.is_valid():
            coop_proposal = review_serializer.save()
        else: 
            self.fail(review_serializer.errors)

        self.assertEqual(CoopProposal.objects.count(), 3)
        self.assertEqual(CoopPublic.objects.count(), 1)
        self.assertEqual(CoopX.objects.count(), 2)
        self.assertEqual(CoopType.objects.count(), 5)
        self.assertEqual(ContactMethod.objects.count(), 12)
        self.assertEqual(PersonX.objects.count(), 6)
        self.assertEqual(CoopAddressTagsX.objects.count(), 5)
        self.assertEqual(Address.objects.count(), 5)

        self.assertEqual(CoopProposal.objects.filter(proposal_status="PENDING").count(), 0)
        self.assertEqual(CoopProposal.objects.filter(proposal_status="APPROVED").count(), 3)
        self.assertEqual(CoopProposal.objects.filter(proposal_status="REJECTED").count(), 0)

        self.assertEqual(CoopX.objects.filter(status="ACTIVE").count(), 0)
        self.assertEqual(CoopX.objects.filter(status="PROPOSAL").count(), 0)
        self.assertEqual(CoopX.objects.filter(status="ARCHIVED").count(), 2)

        self.assertEqual(CoopPublic.objects.filter(status="ACTIVE").count(), 0)
        self.assertEqual(CoopPublic.objects.filter(status="REMOVED").count(), 1)

        print( serialize('json', CoopProposal.objects.all()) )
        print( serialize('json', CoopX.objects.all()) )
        print( serialize('json', CoopPublic.objects.all()) )