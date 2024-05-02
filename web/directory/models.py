from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models import Prefetch
from django.utils.timezone import now
from django.conf import settings

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = PhoneNumberField(blank=True)
    github_username = models.CharField(max_length=165, blank=True)

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
        
class Address(models.Model):
    street_address = models.CharField(max_length=120)
    city = models.CharField(max_length=165)
    county = models.CharField(max_length=165, null=True)
    state = models.CharField(max_length=8)
    postal_code = models.CharField(max_length=10)
    country = models.CharField(max_length=2, default="US")
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Addresses"

    def __str__(self):
        if self.latitude and self.longitude:
            return "%s, %s %s %s, %s (%s, %s)" % (self.street_address, self.city, self.state, self.postal_code, self.country, self.latitude, self.longitude) 
        else:
            return "%s, %s %s %s, %s" % (self.street_address, self.city, self.state, self.postal_code, self.country) 

class AddressCache(models.Model):
    query = models.CharField(max_length=320)
    response = models.JSONField()
    place_id = models.CharField(max_length=50)

class CoopAddressTags(models.Model):
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    is_public = models.BooleanField(default=True, null=False)

class Person(models.Model):
    first_name = models.CharField(max_length=250, null=False)
    last_name = models.CharField(max_length=250, null=False)
    contact_methods = models.ManyToManyField(ContactMethod)
    is_public = models.BooleanField(default=True, null=False)

#============================================================================

class CoopPublic(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        REMOVED = 'REMOVED', _('Removed')
    status = models.CharField( null=False, max_length=8, choices=Status.choices, default="ACTIVE" )
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, related_name="created")
    created_datetime = models.DateTimeField(null=True)
    last_modified_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, related_name="last_modified")
    last_modified_datetime = models.DateTimeField(null=True)

class Coop(models.Model):
    # Metadata Fields
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        PROPOSAL = 'PROPOSAL', _('Proposal')
        ARCHIVED = 'ARCHIVED', _('Archived')
    status = models.CharField( null=False, max_length=8, choices=Status.choices, default="ACTIVE" )
    coop_public = models.ForeignKey(CoopPublic, on_delete=models.DO_NOTHING, null=True)

    # Simple Fields
    name = models.CharField(max_length=250, null=True)
    web_site = models.TextField(null=True)
    description = models.TextField(null=True)
    is_public = models.BooleanField(default=True, null=False)
    scope = models.TextField(null=True)
    tags = models.TextField(null=True)

    # Object Fields
    types = models.ManyToManyField(CoopType)
    contact_methods = models.ManyToManyField(ContactMethod)
    people = models.ManyToManyField(Person)
    addresses = models.ManyToManyField(CoopAddressTags)

class CoopProposal(models.Model):
    class ProposalStatusEnum(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected') 
    proposal_status = models.CharField( null=False, max_length=8, choices=ProposalStatusEnum.choices )
    class OperationTypes(models.TextChoices):
        CREATE = 'CREATE', _('Create')
        UPDATE = 'UPDATE', _('Update')
        DELETE = 'DELETE', _('Delete')
    operation = models.CharField( null=False, max_length=6, choices=OperationTypes.choices )
    change_summary = models.JSONField("Change Summary")
    review_notes = models.TextField(null=True, blank=True)
    coop_public = models.ForeignKey(CoopPublic, on_delete=models.DO_NOTHING, null=True)
    requested_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, related_name="requested")
    requested_datetime = models.DateTimeField()
    reviewed_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, related_name="reviewed")
    reviewed_datetime = models.DateTimeField(null=True)
    coop = models.ForeignKey(Coop, on_delete=models.DO_NOTHING, null=True)

