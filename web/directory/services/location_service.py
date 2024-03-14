from directory.models import Address, AddressCache
from django.core.exceptions import ObjectDoesNotExist
from geopy.geocoders import Nominatim
import re
import json

def preprocess_street_address(address:Address):
    unit_number_pattern = re.compile(r'\b(?:apt|unit|suite|office|room)\b\s*[#\d-]*', re.IGNORECASE)
    cleaned_address = re.sub(unit_number_pattern, '', address)
    cleaned_address = ' '.join(cleaned_address.split())
    return cleaned_address

class LocationService(object):
    def __init__(self, address:Address):
        self.address = address
        self.geo_response = None
        self._fetch_geo_response()

    def _fetch_geo_response(self):
        street_address_cleaned = preprocess_street_address(self.address.street_address)
        query = "%s, %s %s %s" % (street_address_cleaned, self.address.city, self.address.state, self.address.postal_code)

        try:
            cached_address = AddressCache.objects.get(query=query)
        except ObjectDoesNotExist as e:
            cached_address = None

        if cached_address:
            self.geo_response = json.loads(cached_address.response)
        else:
            service = Nominatim(user_agent="chicommons")
            geocode = service.geocode(query=query, exactly_one=True, addressdetails=True, language='en', country_codes='US', timeout=30)
            if not geocode:
                raise Exception("Address could not be geocoded: %s" %(self.address))
            self.geo_response = geocode.raw
            response_json = json.dumps(self.geo_response, indent=4, sort_keys=True)
            AddressCache.objects.create( query=query, response=response_json, place_id=self.geo_response["place_id"])

    def get_coords(self) -> tuple[float, float]:
        if self.geo_response == None:
            self._fetch_geo_response()
        
        if self.geo_response["lat"] and self.geo_response["lon"]:
            return (self.geo_response['lat'], self.geo_response['lon'])
        else:
            raise Exception("Unexpected response format for geocode_task: %s" %(self.geo_response))
    
    def save_coords(self): 
        if self.geo_response == None:
            self._fetch_geo_response()
        
        latitude, longitude = self.get_coords()

        if latitude and longitude:
            self.address.latitude=latitude
            self.address.longitude=longitude
            self.address.save()
        else:
            raise Exception("save_coords failed")