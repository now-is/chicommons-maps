from directory.models import CoopProposal, CoopPublic, CoopX, CoopType, ContactMethod, PersonX, CoopAddressTags, Address, CoopAddressTagsX
from directory.serializers import CoopProposalToCreateSerializer, CoopProposalReviewSerializer, CoopProposalToUpdateSerializer
from rest_framework.test import APITestCase
import json
from unittest.mock import patch, MagicMock
from directory.services.location_service import LocationService
from ratelimit import limits, RateLimitException
import datetime

class TestCoopX(APITestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):
        self.create_data = {
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

    def test_full(self):
        # ==============================
        #   Create proposal to Create
        # ==============================
        coop_proposal_to_create_serializer = CoopProposalToCreateSerializer(data=self.create_data)
        if coop_proposal_to_create_serializer.is_valid():
            coop_create_proposal = coop_proposal_to_create_serializer.save()
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

        self.assertEqual(coop_create_proposal.operation, "CREATE")
        self.assertEqual(coop_create_proposal.proposal_status, "PENDING")
        self.assertIsNone(coop_create_proposal.coop_public)

        coop = coop_create_proposal.coop
        self.assertEqual(coop.name, self.create_data["coop"]["name"])
        self.assertEqual(coop.web_site, self.create_data["coop"]["web_site"])
        self.assertEqual(coop.description, self.create_data["coop"]["description"])
        self.assertEqual(coop.is_public, self.create_data["coop"]["is_public"])
        self.assertEqual(coop.scope, self.create_data["coop"]["scope"])
        self.assertEqual(coop.tags, self.create_data["coop"]["tags"])

        coop_types = coop_create_proposal.coop.types.all()
        self.assertEqual(len(coop_types), 2)
        self.assertEqual(coop_types[0].name, self.create_data["coop"]["types"][0]["name"])
        self.assertEqual(coop_types[1].name, self.create_data["coop"]["types"][1]["name"])

        contact_methods = coop_create_proposal.coop.contact_methods.all()
        self.assertEqual(len(contact_methods), 2)
        self.assertEqual(contact_methods[0].email, self.create_data["coop"]["contact_methods"][0]["email"])
        self.assertEqual(contact_methods[0].phone, None)
        self.assertEqual(contact_methods[1].email, None)
        self.assertEqual(contact_methods[1].phone, self.create_data["coop"]["contact_methods"][1]["phone"])

        people = coop_create_proposal.coop.people.all()
        self.assertEqual(len(people), len(self.create_data["coop"]["people"]))
        for i in range(len(self.create_data["coop"]["people"])):
            self.assertEqual(people[i].first_name, self.create_data["coop"]["people"][i]["first_name"])
            self.assertEqual(people[i].last_name, self.create_data["coop"]["people"][i]["last_name"])
            people_contactmethods = people[i].contact_methods.all()
            for j in range(len(self.create_data["coop"]["people"][i]["contact_methods"])):
                if self.create_data["coop"]["people"][i]["contact_methods"][j]["type"]=="EMAIL":
                    self.assertEqual(people_contactmethods[j].email, self.create_data["coop"]["people"][i]["contact_methods"][j]["email"])
                if self.create_data["coop"]["people"][i]["contact_methods"][j]["type"]=="PHONE":
                    self.assertEqual(people_contactmethods[j].phone, self.create_data["coop"]["people"][i]["contact_methods"][j]["phone"])

        addresses = coop_create_proposal.coop.addresses.all()
        self.assertEqual(len(addresses), len(self.create_data["coop"]["addresses"]))
        for i in range(len(self.create_data["coop"]["addresses"])):
            self.assertEqual(addresses[i].address.street_address, self.create_data["coop"]["addresses"][i]["address"]["street_address"])
            self.assertEqual(addresses[i].address.city, self.create_data["coop"]["addresses"][i]["address"]["city"])
            self.assertEqual(addresses[i].address.state, self.create_data["coop"]["addresses"][i]["address"]["state"])
            self.assertEqual(addresses[i].address.postal_code, self.create_data["coop"]["addresses"][i]["address"]["postal_code"])
            self.assertEqual(addresses[i].address.country, self.create_data["coop"]["addresses"][i]["address"]["country"])

        # ==============================
        #   Review proposal
        # ==============================
        approval_data = {
            'id': coop_create_proposal.id,
            'proposal_status': "APPROVED",
            'review_notes': "lgtm"
        }
        review_serializer = CoopProposalReviewSerializer(coop_create_proposal, data=approval_data)
        if review_serializer.is_valid():
            coop_create_proposal = review_serializer.save()
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

        self.assertEqual(coop_create_proposal.operation, "CREATE")
        self.assertEqual(coop_create_proposal.proposal_status, approval_data["proposal_status"])
        self.assertEqual(coop_create_proposal.review_notes, approval_data["review_notes"])
        self.assertIsNotNone(coop_create_proposal.coop_public)

        # ==============================
        #   Create proposal to Update
        # ==============================
        update_data = {
            "coop_public_id": coop_create_proposal.coop_public.id,
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

        coop_update_serializer = CoopProposalToUpdateSerializer(data=update_data)
        if coop_update_serializer.is_valid():
            coop_update_proposal = coop_update_serializer.save()
        else: 
            self.fail(coop_update_serializer.errors)

        self.assertEqual(CoopProposal.objects.count(), 2)
        self.assertEqual(CoopPublic.objects.count(), 1)
        self.assertEqual(CoopX.objects.count(), 2)
        self.assertEqual(CoopType.objects.count(), 5)
        self.assertEqual(ContactMethod.objects.count(), 12)
        self.assertEqual(PersonX.objects.count(), 6)
        self.assertEqual(CoopAddressTagsX.objects.count(), 5)
        self.assertEqual(Address.objects.count(), 5)

        self.assertEqual(coop_update_proposal.operation, "UPDATE")
        self.assertEqual(coop_update_proposal.proposal_status, "PENDING")
        self.assertIsNotNone(coop_update_proposal.coop_public)

        coop = coop_update_proposal.coop
        self.assertEqual(coop.name, update_data["coop"]["name"])
        self.assertEqual(coop.web_site, update_data["coop"]["web_site"])
        self.assertEqual(coop.description, update_data["coop"]["description"])
        self.assertEqual(coop.is_public, update_data["coop"]["is_public"])
        self.assertEqual(coop.scope, update_data["coop"]["scope"])
        self.assertEqual(coop.tags, update_data["coop"]["tags"])

        coop_types = coop_update_proposal.coop.types.all()
        self.assertEqual(len(coop_types), 3)
        self.assertEqual(coop_types[0].name, update_data["coop"]["types"][0]["name"])
        self.assertEqual(coop_types[1].name, update_data["coop"]["types"][1]["name"])
        self.assertEqual(coop_types[2].name, update_data["coop"]["types"][2]["name"])

        contact_methods = coop_update_proposal.coop.contact_methods.all()
        self.assertEqual(len(contact_methods), 4)
        self.assertEqual(contact_methods[0].email, update_data["coop"]["contact_methods"][0]["email"])
        self.assertEqual(contact_methods[0].phone, None)
        self.assertEqual(contact_methods[1].email, None)
        self.assertEqual(contact_methods[1].phone, update_data["coop"]["contact_methods"][1]["phone"])
        self.assertEqual(contact_methods[2].email, update_data["coop"]["contact_methods"][2]["email"])
        self.assertEqual(contact_methods[2].phone, None)
        self.assertEqual(contact_methods[3].email, None)
        self.assertEqual(contact_methods[3].phone, update_data["coop"]["contact_methods"][3]["phone"])

        people = coop_update_proposal.coop.people.all()
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
        
        addresses = coop_update_proposal.coop.addresses.all()
        self.assertEqual(len(addresses), len(update_data["coop"]["addresses"]))
        for i in range(len(update_data["coop"]["addresses"])):
            self.assertEqual(addresses[i].address.street_address, update_data["coop"]["addresses"][i]["address"]["street_address"])
            self.assertEqual(addresses[i].address.city, update_data["coop"]["addresses"][i]["address"]["city"])
            self.assertEqual(addresses[i].address.state, update_data["coop"]["addresses"][i]["address"]["state"])
            self.assertEqual(addresses[i].address.postal_code, update_data["coop"]["addresses"][i]["address"]["postal_code"])
            self.assertEqual(addresses[i].address.country, update_data["coop"]["addresses"][i]["address"]["country"])

        # ==============================
        #   Review proposal
        # ==============================
        approval_data = {
            'id': coop_update_proposal.id,
            'proposal_status': "APPROVED",
            'review_notes': "lgtm"
        }
        review_serializer = CoopProposalReviewSerializer(coop_update_proposal, data=approval_data)
        if review_serializer.is_valid():
            coop_update_proposal = review_serializer.save()
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

        self.assertEqual(coop_update_proposal.operation, "UPDATE")
        self.assertEqual(coop_update_proposal.proposal_status, approval_data["proposal_status"])
        self.assertEqual(coop_update_proposal.review_notes, approval_data["review_notes"])
        self.assertIsNotNone(coop_update_proposal.coop_public)