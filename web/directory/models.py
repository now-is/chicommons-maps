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
    coop = models.ForeignKey('Coop', related_name='coop_address_tags', on_delete=models.SET_NULL, null=True)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    is_public = models.BooleanField(default=True, null=False)

class Coop(models.Model):
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

class Person(models.Model):
    first_name = models.CharField(max_length=250, null=False)
    last_name = models.CharField(max_length=250, null=False)
    coops = models.ManyToManyField(Coop, related_name='people')
    contact_methods = models.ManyToManyField(ContactMethod)
    is_public = models.BooleanField(default=True, null=False)

#============================================================================

class CoopX(models.Model):
    name = models.CharField(max_length=250, null=True)
    web_site = models.TextField(null=True)
    description = models.TextField(null=True)
    is_public = models.BooleanField(default=True, null=False)
    scope = models.TextField(null=True)
    tags = models.TextField(null=True)
    #requester 
    request_datetime = models.DateTimeField()
    #reviewer
    review_datetime = models.DateTimeField(null=True)
    #types = models.ManyToManyField(CoopType, blank=False)
    #contact_methods = models.ManyToManyField(ContactMethod)

    class Meta:
        abstract = True

class CoopPublic(CoopX):
    class Meta(CoopX.Meta):
        db_table = 'directory_coop_public'

class CoopProposal(CoopX):
    class ProposalStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected') 
    status = models.CharField( null=False, max_length=8, choices=ProposalStatus.choices )
    class OperationTypes(models.TextChoices):
        CREATE = 'CREATE', _('Create')
        UPDATE = 'UPDATE', _('Update')
        DELETE = 'DELETE', _('Delete')
    operation = models.CharField( null=False, max_length=6, choices=OperationTypes.choices )
    change_summary = models.JSONField("Change Summary")
    review_notes = models.TextField(null=True, blank=True)
    coop_public = models.ForeignKey(CoopPublic, on_delete=models.DO_NOTHING, null=True)

    class Meta(CoopX.Meta):
        db_table = 'directory_coop_proposal'  

