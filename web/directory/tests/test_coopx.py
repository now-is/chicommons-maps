from directory.models import CoopProposal, CoopPublic, CoopX
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
        pass

    def test_coopx_CoopProposalcreateserializer(self):
        create_data = {
            "coop": {
                "name": "Test Dave 9999",
                "web_site": "http://www.1871.com/",
                "description": "My Coop Description",
                "is_public": True, # TODO - Confirm biz logic. Should you be able to approve the Coop create in the same call you create it?
                "scope": "Testing", #TODO - What are acceptable values?
                "tags": "tag1, tag2, tag3" #TODO - What are acceptable values?
            }
        }
        coop_proposal_to_create_serializer = CoopProposalToCreateSerializer(data=create_data)
        if coop_proposal_to_create_serializer.is_valid():
            coop_create_proposal = coop_proposal_to_create_serializer.save()
        else: 
            self.fail(coop_proposal_to_create_serializer.errors)

        self.assertEqual(CoopProposal.objects.count(), 1)
        self.assertEqual(CoopPublic.objects.count(), 0)
        self.assertEqual(CoopX.objects.count(), 1)

        self.assertEqual(coop_create_proposal.coop.name, create_data["coop"]["name"])
        self.assertEqual(coop_create_proposal.coop.web_site, create_data["coop"]["web_site"])
        self.assertEqual(coop_create_proposal.coop.description, create_data["coop"]["description"])
        self.assertEqual(coop_create_proposal.coop.is_public, create_data["coop"]["is_public"])
        self.assertEqual(coop_create_proposal.coop.scope, create_data["coop"]["scope"])
        self.assertEqual(coop_create_proposal.coop.tags, create_data["coop"]["tags"])
        self.assertIsNone(coop_create_proposal.coop_public)

        self.assertEqual(coop_create_proposal.operation, "CREATE")
        self.assertEqual(coop_create_proposal.proposal_status, "PENDING")
        print(coop_create_proposal.requested_datetime)

        # ************************************
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
        
        coop_public = CoopPublic.objects.get(id=coop_create_proposal.coop_public.id)
        self.assertEqual(coop_public.coop.id, coop_create_proposal.coop.id)

        coop_create_proposal.refresh_from_db()
        self.assertEqual(coop_create_proposal.operation, "CREATE")
        self.assertEqual(coop_create_proposal.proposal_status, "APPROVED")
        self.assertEqual(coop_create_proposal.coop_public.id, coop_public.id)
        print(coop_create_proposal.requested_datetime)

        # ************************************
        update_data = {
            "coop_public_id" : coop_public.id,
            "coop": {
                "name": "HELLO"
            }
        }

        coop_update_serializer = CoopProposalToUpdateSerializer(data=update_data)
        if coop_update_serializer.is_valid():
            coop_update_proposal = coop_update_serializer.save()
        else: 
            self.fail(coop_update_serializer.errors)

        self.assertEqual(CoopProposal.objects.count(), 2)
        self.assertEqual(CoopPublic.objects.count(), 1)

        self.assertEqual(coop_update_proposal.proposal_status, "PENDING")
        self.assertEqual(coop_update_proposal.operation, "UPDATE")
        print(coop_update_proposal.change_summary)

        self.assertEqual(coop_update_proposal.coop.name, update_data["coop"]["name"])
        self.assertEqual(coop_update_proposal.coop.web_site, create_data["coop"]["web_site"])
        self.assertEqual(coop_update_proposal.coop.description, create_data["coop"]["description"])
        self.assertEqual(coop_update_proposal.coop.is_public, create_data["coop"]["is_public"])
        self.assertEqual(coop_update_proposal.coop.scope, create_data["coop"]["scope"])
        self.assertEqual(coop_update_proposal.coop.tags, create_data["coop"]["tags"])
        self.assertEqual(coop_update_proposal.coop_public.id, coop_public.id)

        self.assertEqual(coop_public.coop.name, create_data["coop"]["name"])

        # ************************************
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

        coop_public = CoopPublic.objects.get(id=coop_update_proposal.coop_public.id)
        self.assertEqual(coop_public.coop.name, update_data["coop"]["name"])
        self.assertEqual(coop_public.coop.web_site, create_data["coop"]["web_site"])
        self.assertEqual(coop_public.coop.description, create_data["coop"]["description"])
        self.assertEqual(coop_public.coop.is_public, create_data["coop"]["is_public"])
        self.assertEqual(coop_public.coop.scope, create_data["coop"]["scope"])
        self.assertEqual(coop_public.coop.tags, create_data["coop"]["tags"])

        coop_update_proposal.refresh_from_db()
        self.assertEqual(coop_update_proposal.operation, "UPDATE")
        self.assertEqual(coop_update_proposal.proposal_status, "APPROVED")
        self.assertEqual(coop_update_proposal.coop_public.id, coop_public.id)
        print(coop_update_proposal.requested_datetime)