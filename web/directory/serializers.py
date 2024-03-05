from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework import serializers
from rest_framework import serializers
from directory.models import Coop, CoopType, ContactMethod, Person, CoopAddressTags
from address.models import Address, Locality, State, Country
from .services.location_service import LocationService
import re
from django.utils.timezone import now

class UserSerializer(serializers.HyperlinkedModelSerializer):
    coops = serializers.HyperlinkedRelatedField(many=True, view_name='coop-detail', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'coops']

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

class CountrySerializer(serializers.ModelSerializer):
    name = serializers.CharField()

    class Meta:
        model = Country
        fields = ['id', 'name', 'code']

class StateSerializer(serializers.ModelSerializer):
    country = CountrySerializer()

    class Meta:
        model = State
        fields = ['id', 'code', 'name', 'country']

class LocalitySerializer(serializers.ModelSerializer):
    state = StateSerializer()
    
    class Meta:
        model = Locality
        fields = ['id', 'name', 'postal_code', 'state']


class AddressSerializer(serializers.ModelSerializer):
    locality = LocalitySerializer()

    class Meta:
        model = Address
        fields = ['id', 'street_number', 'route', 'raw', 'formatted', 'latitude', 'longitude', 'locality']

    def create(self, validated_data):
        locality_data = validated_data.pop('locality', {})
        state_data = locality_data.pop('state', {})
        country_data = state_data.pop('country', {})

        try:
            country = Country.objects.get(name=country_data.get('name'))
        except ObjectDoesNotExist:
            raise serializers.ValidationError({'country': 'Country not found.'})

        try:
            state = State.objects.get(code=state_data.get('code'), country=country)
        except ObjectDoesNotExist:
            raise serializers.ValidationError({'state': 'State not found for the given country.'})
        
        locality_data['state'] = state
        locality, _ = Locality.objects.get_or_create(**locality_data)

        validated_data['locality'] = locality
        address_instance = Address.objects.create(**validated_data)
        return address_instance
    
class CoopAddressTagsSerializer(serializers.ModelSerializer):
    address = AddressSerializer(read_only=False)

    class Meta:
        model = CoopAddressTags
        fields = ['id', 'address', 'is_public']
    
    def create(self, validated_data):
        address_data = validated_data.pop('address')
        address_serializer = AddressSerializer(data=address_data)
        if address_serializer.is_valid(raise_exception=True):
            address_instance = address_serializer.save()
        validated_data['address'] = address_instance
        return super().create(validated_data)
    
    def save(self, **kwargs):
        # Extract coop from kwargs and add it to validated_data
        coop = kwargs.pop('coop', None)
        self.validated_data['coop'] = coop
        
        return super().save(**kwargs)  # Calls create() with updated validated_data    

#     #def to_representation(self, instance):
#     #    print("type of instance: %s" % type(instance))
#     #    rep = super().to_representation(instance)
#     #    rep['address'] = AddressSerializer(instance.address).data
#     #    return rep

#     def update(self, instance, validated_data):
#         """
#         Update and return an existing `AddresssField` instance, given the validated data.
#         """
#         instance.is_public = validated_data.get('is_public', instance.is_public)
#         address = validated_data.get('address')
#         instance.address = serializer.create_obj(validated_data=address)
#         instance.save()
#         return instance

#     def create_obj(self, validated_data):
#         address_data = validated_data.pop('address', {})
#         serializer = AddressSerializer()
#         addr = serializer.create_obj(validated_data=address_data)
#         validated_data['address'] = addr
#         coop_object = Coop.objects.get(id=validated_data['coop_id'])
#         return CoopAddressTags.objects.create(coop=coop_object, **validated_data)

class PersonSerializer(serializers.ModelSerializer):
    contact_methods = ContactMethodSerializer(many=True)
    
    class Meta:
        model = Person
        fields = ['id', 'first_name', 'last_name', 'coops', 'contact_methods', 'is_public']
        extra_kwargs = {'coops': {'required': False, 'write_only': True}} 
        #required=False - When creating or updating a person instance the coops field isn't needed in input data.
        #write_only=True -  Coops field not included in serialized read of person instance. But will be when coops are listed. 
      
    def create(self, validated_data):
        contact_methods_data = validated_data.pop('contact_methods', [])
        coops_data = validated_data.pop('coops', None)
        instance = Person.objects.create(**validated_data)
        for item in contact_methods_data:
            contact_method, created = ContactMethod.objects.get_or_create(**item)
            instance.contact_methods.add(contact_method)
        if coops_data:
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

# class ContactMethodField(serializers.PrimaryKeyRelatedField):

#     queryset = ContactMethod.objects

#     def to_internal_value(self, data):
#         if type(data) == dict:
#             contact_method = ContactMethod.objects.create(**data)
#             data = contact_method.pk
#         return super().to_internal_value(data)


# class LocalitySerializer(serializers.ModelSerializer):
#     state = StateSerializer()
#     class Meta:
#         model = Locality
#         fields = ['id', 'name', 'postal_code', 'state']

#     def to_representation(self, instance):
#         rep = super().to_representation(instance)
#         rep['state'] = StateSerializer(instance.state).data
#         return rep

#     def create(self, validated_data):
#         """
#         Create and return a new `Locality` instance, given the validated data.
#         """
#         print("start create locality method.")
#         country_id = validated_data['state']['country']
#         validated_data['state'] = validated_data['state'].id
#         print("\n\n\n\n****####\n\n", validated_data, "\n\n\n\n")
#         return Locality.objects.create(**validated_data)

#     def update(self, instance, validated_data):
#         """
#         Update and return an existing `Locality` instance, given the validated data.
#         """
#         print("\n\n\n\nupdating address entity \n\n\n\n")
#         instance.name = validated_data.get('name', instance.name)
#         instance.postal_code = validated_data.get('postal_code', instance.name)
#         state = validated_data.get('state', instance.name)
#         instance.state_id = state.id
#         instance.save()
#         return instance


# class CoopAddressTagsSerializer(serializers.ModelSerializer):
#     address = AddressSerializer()

#     class Meta:
#         model = CoopAddressTags
#         fields = ['id', 'address', 'is_public']

#     #def to_representation(self, instance):
#     #    print("type of instance: %s" % type(instance))
#     #    rep = super().to_representation(instance)
#     #    rep['address'] = AddressSerializer(instance.address).data
#     #    return rep

#     def update(self, instance, validated_data):
#         """
#         Update and return an existing `AddresssField` instance, given the validated data.
#         """
#         instance.is_public = validated_data.get('is_public', instance.is_public)
#         address = validated_data.get('address')
#         instance.address = serializer.create_obj(validated_data=address)
#         instance.save()
#         return instance

#     def create_obj(self, validated_data):
#         address_data = validated_data.pop('address', {})
#         serializer = AddressSerializer()
#         addr = serializer.create_obj(validated_data=address_data)
#         validated_data['address'] = addr
#         coop_object = Coop.objects.get(id=validated_data['coop_id'])
#         return CoopAddressTags.objects.create(coop=coop_object, **validated_data)

# class PersonSerializer(serializers.ModelSerializer):
#     contact_methods = ContactMethodField(many=True)

#     class Meta:
#         model = Person
#         fields = ['id', 'first_name', 'last_name', 'coops', 'contact_methods', 'is_public']

#     def to_representation(self, instance):
#         rep = super().to_representation(instance)
#         rep['contact_methods'] = ContactMethodSerializer(instance.contact_methods.all(), many=True).data
#         return rep

#     def create(self, validated_data):
#         #"""
#         #Create and return a new `Snippet` instance, given the validated data.
#         #"""
#         instance = super().create(validated_data)
#         return instance

#     def update(self, instance, validated_data):
#         """
#         Update and return an existing `Coop` instance, given the validated data.
#         """
#         instance.first_name = validated_data.get('first_name', instance.first_name)
#         instance.last_name = validated_data.get('last_name', instance.last_name)
#         coops = validated_data.pop('coops', {})
#         for coop in coops:
#             coop_obj = Coop.objects.get(pk=coop)
#             instance.coops.add(coop)
#         contact_methods = validated_data.pop('contact_methods', {})
#         instance.contact_methods.clear()
#         for contact_method in contact_methods:
#             print("contact method:",contact_method)
#             print("email:",contact_method.email)
#             contact_method_obj = ContactMethod.objects.create(**contact_method)
#             instance.contact_methods.add(contact_method)
#         instance.save()
#         return instance

# class CoopSerializer(serializers.ModelSerializer):
#     types = CoopTypeSerializer(many=True, allow_empty=False)
#     coopaddresstags_set = CoopAddressTagsSerializer(many=True)
#     contact_methods = ContactMethodSerializer(many=True)
#     #phone = ContactMethodPhoneSerializer(many=True)
#     #email = ContactMethodEmailSerializer(many=True)
#     rec_updated_by = UserSerializer(many=True)

#     class Meta:
#         model = Coop
#         fields = ['name', 'description', 'types', 'phone', 'email', 'web_site', 'coopaddresstags_set', 'proposed_changes', 'approved', 'reject_reason', 'coop_public', 'status', 'scope', 'tags', 'rec_source', 'rec_updated_by', 'rec_updated_date', 'people']

#     def to_representation(self, instance):
#         rep = super().to_representation(instance)
#         rep['types'] = CoopTypeSerializer(instance.types.all(), many=True).data
#         rep['coopaddresstags_set'] = CoopAddressTagsSerializer(instance.coopaddresstags_set.all(), many=True).data
#         rep['rec_updated_by'] = UserSerializer(instance.rec_updated_by.all(), many=True).data
#         rep['people'] = PersonSerializer(instance.people.all(), many=True).data
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
#         instance.approved = validated_data.pop('approved', None)
#         instance.reject_reason = validated_data.pop('reject_reason', None)
#         instance.save()
#         for address in addresses:
#             serializer = CoopAddressTagsSerializer()
#             address['coop_id'] = instance.id
#             addr_tag = serializer.create_obj(validated_data=address)
#             result = addr_tag.save()
#             instance.coopaddresstags_set.add(addr_tag)
#         return instance

#     # Set address coordinate data
#     @staticmethod
#     def update_coords(address):
#         svc = LocationService()
#         svc.save_coords(address)

# class CoopProposedChangeSerializer(serializers.ModelSerializer):
#     """
#     This Coop serializer handles proposed changes to a coop.
#     """
#     class Meta:
#         model = Coop
#         fields = ['id', 'proposed_changes']

#     def to_representation(self, instance):
#         rep = super().to_representation(instance)
#         #rep['types'] = CoopTypeSerializer(instance.types.all(), many=True).data
#         #rep['coopaddresstags_set'] = CoopAddressTagsSerializer(instance.coopaddresstags_set.all(), many=True).data
#         return rep

#     #def to_representation(self, instance):
#     #    rep = super().to_representation(instance)
#     #    rep['addresses'] = AddressSerializer(instance.addresses.all(), many=True).data
#     #    return rep


# class CoopSearchSerializer(serializers.ModelSerializer):
#     """
#     This Coop serializer contains a scaled down version of the model to streamline
#     bandwidth used and processing.
#     """
#     types = CoopTypeSerializer(many=True, allow_empty=False)

#     class Meta:
#         model = Coop
#         fields = 'id', 'name', 'approved', 'coopaddresstags_set', 'phone', 'email', 'web_site', 'types'

#     def to_representation(self, instance):
#         rep = super().to_representation(instance)
#         rep['coopaddresstags_set'] = CoopAddressTagsSerializer(instance.coopaddresstags_set.all(), many=True).data
#         rep['phone'] = ContactMethodSerializer(instance.phone.all(), many=True).data
#         rep['email'] = ContactMethodSerializer(instance.email.all(), many=True).data
#         return rep

# class ValidateNewCoopSerializer(serializers.Serializer):
#     # Set all fields as not required and allow_blank=true, so we can combine all validation into one step
#     id=serializers.CharField(required=False, allow_blank=True)
#     coop_name=serializers.CharField(required=False, allow_blank=True)
#     street=serializers.CharField(required=False, allow_blank=True)
#     address_public=serializers.CharField(required=False, allow_blank=True)
#     city=serializers.CharField(required=False, allow_blank=True)
#     state=serializers.CharField(required=False, allow_blank=True)
#     zip=serializers.CharField(required=False, allow_blank=True)
#     county=serializers.CharField(required=False, allow_blank=True)
#     country=serializers.CharField(required=False, allow_blank=True)
#     websites=serializers.CharField(required=False, allow_blank=True)
#     contact_name=serializers.CharField(required=False, allow_blank=True)
#     contact_name_public=serializers.CharField(required=False, allow_blank=True)
#     contact_email=serializers.CharField(required=False, allow_blank=True)
#     contact_email_public=serializers.CharField(required=False, allow_blank=True)
#     contact_phone=serializers.CharField(required=False, allow_blank=True)
#     contact_phone_public=serializers.CharField(required=False, allow_blank=True)
#     entity_types=serializers.CharField(required=False, allow_blank=True)
#     scope=serializers.CharField(required=False, allow_blank=True)
#     tags=serializers.CharField(required=False, allow_blank=True)
#     desc_english=serializers.CharField(required=False, allow_blank=True)
#     desc_other=serializers.CharField(required=False, allow_blank=True)
#     req_reason=serializers.CharField(required=False, allow_blank=True)

#     def validate(self, data):
#         """
#         Validation of start and end date.
#         """
#         errors = {}

#         # required fields
#         required_fields = ['coop_name', 'websites', 'contact_name', 'contact_name_public', 'entity_types', 'req_reason']
#         for field in required_fields:
#             if not data[field]:
#                 errors[field] = 'This field is required.'

#         # contact info
#         contact_email = data['contact_email'] if 'contact_email' in data else None
#         contact_phone = data['contact_phone'] if 'contact_phone' in data else None
#         if not contact_email and not contact_phone:
#             errors['contact'] = 'Either contact phone or contact email is required.'

#         if errors:
#             raise serializers.ValidationError(errors)

#         return data


class UserSigninSerializer(serializers.Serializer):
    username = serializers.CharField(required = True)
    password = serializers.CharField(required = True)


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

#     # Set address coordinate data
#     @staticmethod
#     def update_coords(address):
#         svc = LocationService()
#         svc.save_coords(address)

# class PersonWithCoopSerializer(serializers.ModelSerializer):
#     coops = CoopSerializer(many=True, read_only=True)
#     contact_methods = ContactMethodField(many=True)

#     class Meta:
#         model = Person
#         fields = ['id', 'first_name', 'last_name', 'coops', 'contact_methods', 'is_public']

#     def to_representation(self, instance):
#         rep = super().to_representation(instance)
#         rep['coops'] = CoopSerializer(instance.coops.all(), many=True).data
#         rep['contact_methods'] = ContactMethodSerializer(instance.contact_methods.all(), many=True).data
#         return rep

#     def create(self, validated_data):
#         #"""
#         #Create and return a new `Snippet` instance, given the validated data.
#         #"""
#         instance = super().create(validated_data)
#         return instance

#     def update(self, instance, validated_data):
#         """
#         Update and return an existing `Coop` instance, given the validated data.
#         """
#         instance.first_name = validated_data.get('first_name', instance.first_name)
#         instance.last_name = validated_data.get('last_name', instance.last_name)
#         coops = validated_data.pop('coops', {})
#         for coop in coops:
#             coop_obj = Coop.objects.get(pk=coop)
#             instance.coops.add(coop)
#         contact_methods = validated_data.pop('contact_methods', {})
#         instance.contact_methods.clear()
#         for contact_method in contact_methods:
#             print("contact method:",contact_method)
#             print("email:",contact_method.email)
#             contact_method_obj = ContactMethod.objects.create(**contact_method)
#             instance.contact_methods.add(contact_method)
#         instance.save()
#         return instance
