from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models import Prefetch
from django.utils.timezone import now

class ContactMethod(models.Model):
    class ContactTypes(models.TextChoices):
        EMAIL = 'EMAIL', _('Email')
        PHONE = 'PHONE', _('Phone')

    is_public = models.BooleanField(default=True, null=False)
    type = models.CharField(
        null=False,
        max_length=5,
        choices=ContactTypes.choices,
    )
    phone = PhoneNumberField(null=True)
    email = models.EmailField(null=True)

class CoopType(models.Model):
    name = models.CharField(max_length=200, null=False) 

    class Meta:
        # Creates a new unique constraint with the `name` field
        constraints = [models.UniqueConstraint(fields=['name'], name='coop_type_unq')]

# class CoopManager(models.Manager):
#     # Look up by coop type
#     def get_by_type(self, type):
#         qset = Coop.objects.filter(types__name=type,
#                                    enabled=True)
#         return qset

#     def find(
#         self,
#         partial_name,
#         types_arr=None,
#         enabled=None,
#         city=None,
#         zip=None,
#         street=None,
#         state_abbrev=None
#     ):
#         """
#         Lookup coops by varying criteria.
#         """
#         q = Q()
#         if partial_name:
#             q &= Q(name__icontains=partial_name)
#         if enabled != None:
#             q &= Q(enabled=enabled)
#         if types_arr != None:
#             filter = Q(
#                 *[('types__name', type) for type in types_arr],
#                 _connector=Q.OR
#             )
#             q &= filter
#         if street != None:
#             q &= Q(addresses__raw__icontains=street)
#         if city != None:
#             q &= Q(addresses__locality__name__iexact=city)
#         if zip != None:
#             q &= Q(addresses__locality__postal_code=zip)
#         if state_abbrev != None:
#             q &= Q(addresses__locality__state__code=state_abbrev)
#             q &= Q(addresses__locality__state__country__code="US")

#         addressTagsPrefetcher = Prefetch('coopaddresstags_set', queryset=CoopAddressTags.objects.select_related('address', 'address__locality', 'address__locality__state', 'address__locality__state__country'))
#         queryset = Coop.objects.filter(q).prefetch_related(addressTagsPrefetcher, 'types')
        
#         phonePrefetcher = Prefetch('phone', queryset=ContactMethod.objects.all())
#         emailPrefetcher = Prefetch('email', queryset=ContactMethod.objects.all())
#         queryset = queryset.prefetch_related(phonePrefetcher).prefetch_related(emailPrefetcher)
#         print(queryset.query)
#         return queryset

#     # Meant to look up coops case-insensitively by part of a type
#     def contains_type(self, types_arr):
#         filter = Q(
#             *[('types__name__icontains', type) for type in types_arr],
#             _connector=Q.OR
#         )
#         queryset = Coop.objects.filter(filter, enabled=True)
#         return queryset
        
class Address(models.Model):
    street_address = models.CharField(max_length=120)
    city = models.CharField(max_length=165)
    state = models.CharField(max_length=8)
    postal_code = models.CharField(max_length=10)
    country = models.CharField(max_length=2, default="US")
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Addresses"

class CoopAddressTags(models.Model):
    coop = models.ForeignKey('Coop', related_name='coop_address_tags', on_delete=models.SET_NULL, null=True)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    is_public = models.BooleanField(default=True, null=False)

class Coop(models.Model):
    #objects = CoopManager()
    name = models.CharField(max_length=250, null=False)
    types = models.ManyToManyField(CoopType, blank=False)
    enabled = models.BooleanField(default=True, null=False)
    contact_methods = models.ManyToManyField(ContactMethod)
    web_site = models.TextField()
    description = models.TextField(null=True)
    approved = models.BooleanField(default=False, null=True)
    proposed_changes = models.JSONField("Proposed Changes", null=True)
    reject_reason = models.TextField(null=True)
    coop_public = models.BooleanField(default=True, null=False)
    status = models.TextField(null=True)
    scope = models.TextField(null=True)
    tags = models.TextField(null=True)
    rec_source = models.TextField(null=True)
    rec_updated_by = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    rec_updated_date = models.DateTimeField(default=now, blank=True)

    def apply_proposed_changes(self):
        proposed = self.proposed_changes
        self.name = proposed.get('name')
        self.web_site = proposed.get('web_site')
        for type in proposed.get('types'):
            self.types.add(CoopType.objects.get(name=type))
        self.save()

class Person(models.Model):
    first_name = models.CharField(max_length=250, null=False)
    last_name = models.CharField(max_length=250, null=False)
    coops = models.ManyToManyField(Coop, related_name='people')
    contact_methods = models.ManyToManyField(ContactMethod)
    is_public = models.BooleanField(default=True, null=False)