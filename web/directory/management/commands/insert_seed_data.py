from django.core.management import call_command
from django.core.management.base import BaseCommand

from directory.models import Coop, CoopType, Address, CoopAddressTags, ContactMethod, AddressCache, Person

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('seed_file', type=str, nargs='?', default='web/directory/fixtures/seed_test.yaml')
        parser.add_argument('delete_existing_data', type=bool, nargs='?', default='true')

    def handle(self, *args, **options):
        seed_data_file = options.get('seed_file')
        print("seed file %s" % seed_data_file)
        delete_existing_data = options.get('delete_existing_data', False)

        if delete_existing_data:
            self.stdout.write('Deleting existing data')
            if Person.objects.exists():
                Person.objects.all().delete()
            if CoopType.objects.exists():
                CoopType.objects.all().delete()
            if ContactMethod.objects.exists():
                ContactMethod.objects.all().delete()
            if AddressCache.objects.exists():
                AddressCache.objects.all().delete()
            if Address.objects.exists():
                Address.objects.all().delete()
            if CoopAddressTags.objects.exists():
                CoopAddressTags.objects.all().delete()
            if Coop.objects.exists():
                Coop.objects.all().delete()
        self.stdout.write('Seeding initial data')
        call_command('loaddata', seed_data_file)

