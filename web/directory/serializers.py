from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers, exceptions
from directory.models import Coop, CoopType, ContactMethod, Person, CoopAddressTags, Address, CoopProposal, CoopPublic, CoopX, PersonX, CoopAddressTagsX
from django.utils.timezone import now
from directory.services.location_service import LocationService
import json

User = get_user_model()

# class UserSerializer(serializers.HyperlinkedModelSerializer):
#     coops = serializers.HyperlinkedRelatedField(many=True, view_name='coop-detail', read_only=True)

#     class Meta:
#         model = User
#         fields = ['id', 'username', 'coops']

# TODO - Don't let it create duplicate rows
class CoopTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoopType
        fields = ['name']

class ContactMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMethod
        fields = ['id', 'type', 'is_public', 'phone', 'email']
    
    def validate(self, data):
        if not data.get('email') and not data.get('phone'):
            raise serializers.ValidationError("Either an email or a phone number must be provided.")
        elif data.get('email') and data.get('phone'):
            raise serializers.ValidationError("Either an email or a phone number must be provided.")
        return data
    
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'street_address', 'city', 'county', 'state', 'postal_code', 'country', 'latitude', 'longitude']
    
    def create(self, validated_data):
        instance = Address.objects.create(**validated_data)
        if not instance.latitude or not instance.longitude or not instance.county:
            loc_svc = LocationService(instance)
            if not instance.latitude or not instance.longitude:
                loc_svc.save_coords()
            if not instance.county:
                loc_svc.save_county()
        return instance

    def update(self, instance, validated_data):
        address_change = any(
            getattr(instance, field) != validated_data[field] 
            for field in ['street_address', 'city', 'state', 'postal_code', 'country']
        )

        override_county = validated_data.get('county')
        if override_county:
            instance.county = validated_data.get('county')

        override_coords = validated_data.get('latitude') and validated_data.get('longitude')
        if override_coords:
            instance.latitude = validated_data.get('latitude')
            instance.longitude = validated_data.get('longitude')
        
        update_geocode = address_change and not ( override_county and override_coords )

        instance.street_address = validated_data.get('street_address', instance.street_address)
        instance.city = validated_data.get('city', instance.city)
        instance.state = validated_data.get('state', instance.state)
        instance.postal_code = validated_data.get('postal_code', instance.postal_code)
        instance.country = validated_data.get('country', instance.country)
        instance.save()

        if update_geocode:
            loc_svc = LocationService(instance)
            if not override_county:
                loc_svc.save_county()
            if not override_coords:
                loc_svc.save_coords()

        return instance
  
class CoopAddressTagsSerializer(serializers.ModelSerializer):
    address = AddressSerializer(read_only=False)

    class Meta:
        model = CoopAddressTags
        fields = ['id', 'address', 'is_public']
    
    def create(self, validated_data):
        address_data = validated_data.pop('address')
        instance = CoopAddressTags.objects.create(**validated_data)
        address_serializer = AddressSerializer(data=address_data)
        if address_serializer.is_valid(raise_exception=True):
            instance.address = address_serializer.save()
        instance.save()
        return instance
    
    def update(self, instance, validated_data):
        instance.coop = validated_data.get('coop', instance.coop)
        instance.is_public = validated_data.get('is_public', instance.is_public)
        if 'address' in validated_data:
            instance.address.delete()
            address_data = validated_data.pop('address')
            address_serializer = AddressSerializer(data=address_data)
            if address_serializer.is_valid(raise_exception=True):
                instance.address = address_serializer.save()
        instance.save()
        return instance

class PersonSerializer(serializers.ModelSerializer):
    contact_methods = ContactMethodSerializer(many=True)
    
    class Meta:
        model = Person
        fields = ['id', 'first_name', 'last_name', 'coops', 'contact_methods', 'is_public']
        extra_kwargs = {'coops': {
            'required': False, # When creating or updating a person instance the coops field isn't needed in input data.
            'write_only': True # Coops field not included in serialized read of person instance. But will be when coops are listed.
        }} 
      
    def create(self, validated_data):
        contact_methods_data = validated_data.pop('contact_methods', [])
        coops_data = validated_data.pop('coops', None)
        instance = Person.objects.create(**validated_data)
        for item in contact_methods_data:
            contact_method, created = ContactMethod.objects.get_or_create(**item)
            instance.contact_methods.add(contact_method)
        if coops_data: #TODO: Remove this
            for coop in coops_data:
                instance.coops.add(coop)
        return instance

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.is_public = validated_data.get('is_public', instance.is_public)

        instance.save()

        if 'contact_methods' in validated_data:
            instance.contact_methods.all().delete()
            contact_methods_data = validated_data.pop('contact_methods')
            for item in contact_methods_data:
                contact_method_serializer = ContactMethodSerializer(data=item)
                if contact_method_serializer.is_valid():
                    contact_method = contact_method_serializer.save()
                    instance.contact_methods.add(contact_method)
    
        if 'coops' in validated_data:
            instance.coops.clear()
            coops_data = validated_data.pop('coops')
            for item in coops_data:
                #TODO - Check if Coop is valid
                instance.coops.add(item)
        
        return instance

class CoopSerializer(serializers.HyperlinkedModelSerializer):
    rec_updated_by = serializers.ReadOnlyField(source='rec_updated_by.username')
    types = CoopTypeSerializer(many=True, read_only=False)
    contact_methods = ContactMethodSerializer(many=True, read_only=False, required=False, allow_null=True)
    coop_address_tags = CoopAddressTagsSerializer(many=True, read_only=False, required=False, allow_null=True)
    people = PersonSerializer(many=True, read_only=False, required=False, allow_null=False)
 
    class Meta:
        model = Coop
        fields = ['id', 'name', 'types', 'coop_address_tags', 'people', 'enabled', 'contact_methods', 'web_site', 'description', 'approved', 'proposed_changes', 'reject_reason', 'coop_public', 'status', 'scope', 'tags', 'rec_source', 'rec_updated_by', 'rec_updated_date']

    @transaction.atomic
    def create(self, validated_data):
        types_data = validated_data.pop('types', [])
        contact_methods_data = validated_data.pop('contact_methods', [])
        coop_address_tags_data = validated_data.pop('coop_address_tags', [])
        people_data = validated_data.pop('people', [])
        rec_updated_date = now()

        instance = Coop.objects.create(**validated_data)
        instance.rec_updated_date = rec_updated_date

        for item in types_data:
            coop_type, _ = CoopType.objects.get_or_create(**item)
            instance.types.add(coop_type)

        for item in contact_methods_data:
            contact_method, _ = ContactMethod.objects.get_or_create(**item)
            instance.contact_methods.add(contact_method)

        for tag_data in coop_address_tags_data:
            coop_address_tag_serializer = CoopAddressTagsSerializer(data=tag_data)
            if coop_address_tag_serializer.is_valid(raise_exception=True):
                coop_address_tag_serializer.save(coop=instance)
        
        for person_data in people_data:
            person_serializer = PersonSerializer(data=person_data, context=self.context)
            if person_serializer.is_valid(raise_exception=True):
                person = person_serializer.save()
                person.coops.add(instance)
        
        return instance
    
    @transaction.atomic
    def update(self, instance, validated_data):
        # Update read-only fields
        instance.rec_updated_by = validated_data.get('rec_updated_by')
        instance.rec_updated_date = now()

        # Update simple fields on Coop instance
        instance.name = validated_data.get('name', instance.name)
        instance.enabled = validated_data.get('enabled', instance.enabled)
        instance.web_site = validated_data.get('web_site', instance.web_site)
        instance.description = validated_data.get('description', instance.description)
        instance.approved = validated_data.get('approved', instance.approved)
        instance.proposed_changes = validated_data.get('proposed_changes', instance.proposed_changes)
        instance.reject_reason = validated_data.get('reject_reason', instance.reject_reason)
        instance.coop_public = validated_data.get('coop_public', instance.coop_public)
        instance.status = validated_data.get('status', instance.status)
        instance.scope = validated_data.get('scope', instance.scope)
        instance.tags = validated_data.get('tags', instance.tags)
        instance.rec_source = validated_data.get('rec_source', instance.rec_source)

        instance.save()

        # Handle ManyToManyField for types
        #TODO - Should never allow types to be empty
        if 'types' in validated_data:
            instance.types.clear()
            types_data = validated_data.pop('types')
            for item in types_data:
                coop_type, _ = CoopType.objects.get_or_create(**item)
                instance.types.add(coop_type)

        # Handle related objects for contact_methods
        # Deletes all existing and adds the provided
        if 'contact_methods' in validated_data:
            instance.contact_methods.all().delete()
            contact_methods_data = validated_data.pop('contact_methods')
            for item in contact_methods_data:
                contact_method_serializer = ContactMethodSerializer(data=item)
                if contact_method_serializer.is_valid():
                    contact_method = contact_method_serializer.save()
                    instance.contact_methods.add(contact_method)

        # Handle related objects for addresses
        # Deletes all existing and adds the provided
        if 'coop_address_tags' in validated_data:
            instance.coop_address_tags.all().delete()
            coop_address_tags_data = validated_data.pop('coop_address_tags')
            for item in coop_address_tags_data:
                coop_address_tags_serializer = CoopAddressTagsSerializer(data=item)
                if coop_address_tags_serializer.is_valid():
                    coop_address_tag = coop_address_tags_serializer.save()
                    instance.coop_address_tags.add(coop_address_tag)
        
        # Update people
        # Clear and recreate links to handle removals and additions.
        if 'people' in validated_data:
            people_data = validated_data.pop('people', [])
            existing_person_ids = [person_data.get('id') for person_data in people_data if 'id' in person_data]
            # Remove people not included in the update.
            for person in instance.people.all():
                if person.id not in existing_person_ids:
                    person.coops.remove(instance)
            for person_data in people_data:
                person_id = person_data.get('id')
                if person_id:
                    person_instance = Person.objects.get(id=person_id)
                    person_serializer = PersonSerializer(person_instance, data=person_data, partial=True, context=self.context)
                else:
                    person_serializer = PersonSerializer(data=person_data, context=self.context)
                if person_serializer.is_valid(raise_exception=True):
                    person = person_serializer.save()
                    person.coops.add(instance)

        return instance

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'first_name', 'last_name')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        return user

# class CoopSpreadsheetSerializer(serializers.ModelSerializer):
#     types = CoopTypeSerializer(many=True, allow_empty=False)
#     coopaddresstags_set = CoopAddressTagsSerializer(many=True)
#     phone = ContactMethodPhoneSerializer(many=True)
#     email = ContactMethodEmailSerializer(many=True)
#     rec_updated_by = UserSerializer(many=True)
#     people = PersonSerializer(many=True, read_only=True)

#     class Meta:
#         model = Coop
#         fields = ['id', 'name', 'description', 'types', 'phone', 'email', 'web_site', 'coopaddresstags_set', 'approved', 'reject_reason', 'coop_public', 'status', 'scope', 'tags', 'rec_source', 'rec_updated_by', 'rec_updated_date', 'people']

#     def to_representation(self, instance):
#         rep = super().to_representation(instance)
#         rep['types'] = CoopTypeSerializer(instance.types.all(), many=True).data
#         rep['coopaddresstags_set'] = CoopAddressTagsSerializer(instance.coopaddresstags_set.all(), many=True).data
#         return rep

#     def create(self, validated_data):
#         """
#         Create and return a new `Snippet` instance, given the validated data.
#         """
#         return self.save_obj(validated_data=validated_data)

#     def update(self, instance, validated_data):
#         """
#         Update and return an existing `Coop` instance, given the validated data.
#         """
#         return self.save_obj(instance=instance, validated_data=validated_data)

#     def save_obj(self, validated_data, instance=None):
#         coop_types = validated_data.pop('types', {})
#         addresses = validated_data.pop('coopaddresstags_set', {})
#         phone = validated_data.pop('phone', {})
#         email = validated_data.pop('email', {})
#         if not instance:
#             instance = super().create(validated_data)
#         for item in coop_types:
#             coop_type, _ = CoopType.objects.get_or_create(name=item['name'])
#             instance.types.add(coop_type)
#         instance.phone = ContactMethod.objects.create(type=ContactMethod.ContactTypes.PHONE, **phone)
#         instance.email = ContactMethod.objects.create(type=ContactMethod.ContactTypes.EMAIL, **email)
        
#         instance.name = validated_data.pop('name', None)
#         instance.web_site = validated_data.pop('web_site', None)
#         instance.save()
#         for address in addresses:
#             serializer = CoopAddressTagsSerializer()
#             address['coop_id'] = instance.id
#             addr_tag = serializer.create_obj(validated_data=address)
#             result = addr_tag.save()
#             instance.coopaddresstags_set.add(addr_tag)
#         return instance
    
#============================================================================

class CoopPublicListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoopPublic
        fields = ['id', 'name', 'web_site', 'description', 'is_public', 'status', 'scope', 'tags', 'requested_datetime', 'reviewed_datetime' ]

class CoopProposalListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoopProposal
        fields = ['id', 'name', 'web_site', 'description', 'is_public', 'scope', 'tags', 
                  'proposal_status', 'operation', 'change_summary', 'review_notes']

class PersonXSerializer(serializers.ModelSerializer):
    contact_methods = ContactMethodSerializer(many=True)
    
    class Meta:
        model = PersonX
        fields = ['id', 'first_name', 'last_name', 'contact_methods', 'is_public']
      
    def create(self, validated_data):
        contact_methods_data = validated_data.pop('contact_methods', [])

        instance = PersonX.objects.create(**validated_data)

        for item in contact_methods_data:
            contact_method, _ = ContactMethod.objects.get_or_create(**item)
            instance.contact_methods.add(contact_method)

        return instance

    def update(self, instance, validated_data):
        contact_methods_data = validated_data.pop('contact_methods', [])

        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.is_public = validated_data.get('is_public', instance.is_public)

        instance.save()

        if contact_methods_data:
            instance.contact_methods.clear()
            for item in contact_methods_data:
                contact_method_serializer = ContactMethodSerializer(data=item)
                if contact_method_serializer.is_valid():
                    contact_method = contact_method_serializer.save()
                    instance.contact_methods.add(contact_method)
        
        return instance

class CoopAddressTagsXSerializer(serializers.ModelSerializer):
    address = AddressSerializer(read_only=False)

    class Meta:
        model = CoopAddressTagsX
        fields = ['id', 'address', 'is_public']
    
    def create(self, validated_data):
        address_data = validated_data.pop('address', [])

        instance = CoopAddressTagsX.objects.create(**validated_data)

        address_serializer = AddressSerializer(data=address_data)
        if address_serializer.is_valid(raise_exception=True):
            address = address_serializer.save()
            instance.address = address
            
        instance.save()
        return instance
    
    def update(self, instance, validated_data):
        address_data = validated_data.pop('address', [])

        instance.is_public = validated_data.get('is_public', instance.is_public)

        if address_data:
            instance.address.delete()
            address_serializer = AddressSerializer(data=address_data)
            if address_serializer.is_valid(raise_exception=True):
                address = address_serializer.save()
                instance.address = address
                
        instance.save()
        return instance
        
class CoopXSerializer(serializers.ModelSerializer):
    types = CoopTypeSerializer(many=True, read_only=False, required=False, allow_null=True)
    contact_methods = ContactMethodSerializer(many=True, read_only=False, required=False, allow_null=True)
    people = PersonXSerializer(many=True, read_only=False, required=False, allow_null=False)
    addresses = CoopAddressTagsSerializer(many=True, read_only=False, required=False, allow_null=True)

    class Meta:
        model = CoopX
        fields = "__all__"

    @transaction.atomic
    def create(self, validated_data):
        types_data = validated_data.pop('types', [])
        contact_methods_data = validated_data.pop('contact_methods', [])
        people_data = validated_data.pop('people', [])
        addresses_data = validated_data.pop('addresses',[])

        instance = CoopX.objects.create(**validated_data)

        for item in types_data:
            coop_type, _ = CoopType.objects.get_or_create(**item)
            instance.types.add(coop_type)
        
        for item in contact_methods_data:
            contact_method, _ = ContactMethod.objects.get_or_create(**item)
            instance.contact_methods.add(contact_method)

        for item in people_data:
            person_serializer = PersonXSerializer(data=item)
            if person_serializer.is_valid(raise_exception=True):
                person = person_serializer.save()
                instance.people.add(person)
        
        for item in addresses_data:
            coop_address_tag_serializer = CoopAddressTagsXSerializer(data=item)
            if coop_address_tag_serializer.is_valid(raise_exception=True):
                address = coop_address_tag_serializer.save()
                instance.addresses.add(address)

        return instance
    
    def update(self, instance, validated_data):
        types_data = validated_data.pop('types', [])
        contact_methods_data = validated_data.pop('contact_methods', [])
        people_data = validated_data.pop('people', [])
        addresses_data = validated_data.pop('addresses',[])

        for field, value in validated_data.items():
            setattr(instance, field, value)

        if types_data:
            instance.types.clear()
            for item in types_data:
                coop_type, _ = CoopType.objects.get_or_create(**item)
                instance.types.add(coop_type)
        
        if contact_methods_data:
            instance.contact_methods.clear()#all().delete()
            for item in contact_methods_data:
                contact_method_serializer = ContactMethodSerializer(data=item)
                if contact_method_serializer.is_valid():
                    contact_method = contact_method_serializer.save()
                    instance.contact_methods.add(contact_method)

        if people_data:
            instance.people.clear()
            for person_data in people_data:
                person_serializer = PersonXSerializer(data=person_data)
                if person_serializer.is_valid(raise_exception=True):
                    person = person_serializer.save()
                    instance.people.add(person)

        if addresses_data:
            instance.addresses.clear()
            for item in addresses_data:
                coop_address_tag_serializer = CoopAddressTagsXSerializer(data=item)
                if coop_address_tag_serializer.is_valid(raise_exception=True):
                    address = coop_address_tag_serializer.save()
                    instance.addresses.add(address)
        instance.save()
        return instance
        
class CoopProposalCreateSerializer(serializers.ModelSerializer):
    requested_by = serializers.ReadOnlyField(source='requested_by.username')
    proposal_status = serializers.CharField(read_only=True)
    change_summary = serializers.JSONField(read_only=True)
    requested_datetime = serializers.DateTimeField(read_only=True)
    coop_public_id = serializers.IntegerField(write_only=True, required=False)
    operation = serializers.CharField(write_only=True, required=True)
    coop = CoopXSerializer(many=False, read_only=False, required=False)

    class Meta:
        model = CoopProposal
        fields = '__all__'
    
    def create(self, validated_data):
        operation = validated_data.pop('operation', "")

        if operation not in CoopProposal.OperationTypes:
            raise exceptions.ValidationError("Incorrect operation type.")

        if operation == CoopProposal.OperationTypes.CREATE:
            return self.process_create_operation(validated_data)
        elif operation == CoopProposal.OperationTypes.UPDATE:
            return self.process_update_operation(validated_data)
        elif operation == CoopProposal.OperationTypes.DELETE:
            return self.process_delete_operation(validated_data)
            
    def process_create_operation(self, validated_data):
        # Prepare Data to Create Coop
        coop_data = validated_data.pop('coop', {})
        coop_data["status"] = "PROPOSAL"

        # Prepare Data to Create Coop Proposal
        validated_data["proposal_status"] = "PENDING"
        validated_data["operation"] = "CREATE"
        validated_data["requested_datetime"] = now()
        validated_data["change_summary"] = json.dumps(validated_data, default=str)
        # Create CoopProposal object
        coop_proposal = CoopProposal.objects.create(**validated_data)

        # Create Coop object
        coopx_serializer = CoopXSerializer(data=coop_data)
        if coopx_serializer.is_valid():
            coop_instance = coopx_serializer.save()
            coop_proposal.coop = coop_instance
            coop_proposal.save()
        return coop_proposal
    
    def process_update_operation(self, validated_data):
        # Prepare Data to Create Coop
        coop_data = validated_data.pop('coop', {})
        coop_data["status"] = "PROPOSAL"

        # Prepare Data to Create CoopProposal
        validated_data["proposal_status"] = "PENDING"
        validated_data["operation"] = "UPDATE"
        validated_data["requested_datetime"] = now()
        validated_data["change_summary"] = json.dumps(validated_data, default=str)
        validated_data["coop_public"] = CoopPublic.objects.get(id=validated_data["coop_public_id"])
        # Create CoopProposal object
        coop_proposal = CoopProposal.objects.create(**validated_data)

        # Copy active Coop object. Save as new object.
        try:
            copied_coop = CoopX.objects.get(status="ACTIVE", coop_public_id=validated_data["coop_public_id"])
        except CoopX.MultipleObjectsReturned as e:
            raise CoopX.MultipleObjectsReturned()
        except CoopX.DoesNotExist as e:
            raise CoopX.DoesNotExist()
        copied_coop.pk = None # Setting 'pk' to None creates a new instance when saved
        copied_coop.save()

        # Modify copied coop object with user supplied changes.
        coopx_serializer = CoopXSerializer(copied_coop, data=coop_data)
        if coopx_serializer.is_valid():
            coop_instance = coopx_serializer.save()
            coop_proposal.coop = coop_instance
            coop_proposal.save()

        return coop_proposal

    def process_delete_operation(self, validated_data):
        coop_public_id = validated_data.pop('coop_public_id', {})

        validated_data["proposal_status"] = "PENDING"
        validated_data["operation"] = "DELETE"
        validated_data["requested_datetime"] = now()
        validated_data["change_summary"] = json.dumps(validated_data, default=str)

        coop_proposal = CoopProposal.objects.create(**validated_data)

        coop_proposal.coop_public = CoopPublic.objects.get(status="ACTIVE", id=coop_public_id)
        coop_proposal.save()
        return coop_proposal

class CoopProposalReviewSerializer(serializers.ModelSerializer):
    proposal_status = serializers.ChoiceField(choices=[('APPROVED','Approved'), ('REJECTED', 'Rejected')])
    reviewed_by = serializers.ReadOnlyField(source='reviewed_by.username')
    coop_public_id = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = CoopProposal
        fields = ['id', 'proposal_status', 'review_notes', 'coop_public_id', 'reviewed_by']
    
    def validate(self, attrs):
        if self.instance and (self.instance.proposal_status != CoopProposal.ProposalStatus.PENDING):
            raise exceptions.ValidationError("Only proposals with a 'PENDING' proposal_status can be reviewed and applied.")
        return super().validate(attrs)
    
    def update(self, coop_proposal:CoopProposal, validated_data):
        self._update_coop_proposal(coop_proposal, validated_data)

        if coop_proposal.proposal_status == "REJECTED":
            coop_proposal.save()
            return coop_proposal
        
        coop_public = self._fetch_coop_public(coop_proposal)
        self._update_coop_public(coop_proposal, coop_public)
        if coop_proposal.operation == "CREATE":
            coop_proposal.coop_public = coop_public
            
        self._update_coop(coop_proposal, coop_public)

        coop_proposal.save()
        return coop_proposal

    def _update_coop_proposal(self, coop_proposal, validated_data):
        coop_proposal.proposal_status = validated_data.get('proposal_status')
        coop_proposal.review_notes = validated_data.get('review_notes', "")
        coop_proposal.reviewed_by = validated_data.get('reviewed_by')
        coop_proposal.reviewed_datetime = now()

    def _fetch_coop_public(self, coop_proposal):
        if coop_proposal.operation == "CREATE":
            return CoopPublic()
        elif coop_proposal.operation == "UPDATE":
            return self._get_or_raise_coop_public(coop_proposal)
        elif coop_proposal.operation == "DELETE":
            return self._get_or_raise_coop_public(coop_proposal)

    def _get_or_raise_coop_public(self, coop_proposal):
        try:
            return CoopPublic.objects.get(id=coop_proposal.coop_public.id)
        except CoopPublic.DoesNotExist:
            raise

    def _update_coop_public(self, coop_proposal, coop_public):
        coop_public.last_modified_by = coop_proposal.requested_by
        coop_public.last_modified_datetime = coop_proposal.reviewed_datetime
        if coop_proposal.operation == "CREATE":
            #coop_public.coop = coop_proposal.coop
            coop_public.status = "ACTIVE"
            coop_public.created_by = coop_proposal.requested_by
            coop_public.created_datetime = coop_proposal.reviewed_datetime
        elif coop_proposal.operation == "UPDATE":
            #coop_public.coop = coop_proposal.coop
            pass
        elif coop_proposal.operation == "DELETE":
            #coop_public.coop = None
            coop_public.status = "REMOVED"
        coop_public.save()

    def _update_coop(self, coop_proposal, coop_public):
        coop = coop_proposal.coop
        if coop_proposal.operation == "CREATE":
            coop.status = "ACTIVE"
            coop.coop_public = coop_public
        elif coop_proposal.operation == "UPDATE":
            self._archive_active_coop(coop_proposal)
            coop.status = "ACTIVE"
        elif coop_proposal.operation == "DELETE":
            self._archive_active_coop(coop_proposal)    
            return
        coop.save()

    def _archive_active_coop(self, coop_proposal):
        active_coop = self._get_active_coop(coop_proposal)
        active_coop.status = "ARCHIVED"
        active_coop.save()   

    def _get_active_coop(self, coop_proposal):
        try:
            active_coop = CoopX.objects.get(status="ACTIVE", coop_public_id=coop_proposal.coop_public.id)
        except CoopX.MultipleObjectsReturned as e:
            raise CoopX.MultipleObjectsReturned
        return active_coop
    
    def to_representation(self, instance):
        # We want to return to the user the id of the approved coop without requiring them to navigate the coop_public object.
        # Meta.Fields determines which fields get returned. The coop_public_id field is not part of CoopProposal model which this serializer manipulates.
        # Below, after the serializer finishes its validation of CoopProposal we add a new field to the APIs response to the user.
        ret = super(CoopProposalReviewSerializer, self).to_representation(instance)
        ret['coop_public_id'] = instance.coop_public.id #if instance.coop_public else None
        return ret
