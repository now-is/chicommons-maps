from django.contrib import admin
from .models import Coop, CoopType, CoopAddressTags, ContactMethod, Address, Person

admin.site.register(Coop)
admin.site.register(CoopType)
admin.site.register(CoopAddressTags)
admin.site.register(ContactMethod)
admin.site.register(Address)
admin.site.register(Person)