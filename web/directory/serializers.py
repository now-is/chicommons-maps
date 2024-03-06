from geopy.geocoders import Nominatim
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
    raw = serializers.CharField(write_only=True)
    formatted = serializers.CharField(write_only=True, required=False)
    locality = serializers.CharField(write_only=True)
    state = serializers.CharField(write_only=True)
    postal_code = serializers.CharField(write_only=True)
    country = serializers.CharField(write_only=True, required=False, default="United States")

    class Meta:
        model = Address
        fields = '__all__'

    def validate_country(self, country_name):
        try: 
            country = Country.objects.get(name=country_name)
            return country_name
        except ObjectDoesNotExist:
            raise serializers.ValidationError("Country not found.")
        
    def validate(self, data):
        country_name = data.get('country') # class 'str'        
        country = Country.objects.get(name=country_name)
        state_code = data.pop("state", None) # class 'str'
        if state_code:
            try:
                state = State.objects.get(code=state_code, country=country)
                data['state'] = state_code
            except ObjectDoesNotExist:
                raise serializers.ValidationError({"state": "State not found for the given country."})
        return data
    
    def create(self, validated_data):
        country_name = validated_data.pop('country')
        country = Country.objects.get(name=country_name)

        state_code = validated_data.pop("state", None)
        state = State.objects.get(code=state_code, country=country)
        
        locality_name_data = validated_data.pop("locality", "")
        postal_code_data = validated_data.pop("postal_code", "")
        
        locality_data = {
            'state': state,
            'name': locality_name_data,
            'postal_code': postal_code_data
        }
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
        instance = CoopAddressTags.objects.create(**validated_data)
        address_serializer = AddressSerializer(data=address_data)
        if address_serializer.is_valid(raise_exception=True):
            address_instance = address_serializer.save()
            instance.address = address_instance
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
                address = address_serializer.save()
                instance.address = address
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