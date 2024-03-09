import csv

from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.db.models.functions import Lower
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, generics
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.status import (HTTP_200_OK, HTTP_400_BAD_REQUEST,
                                   HTTP_404_NOT_FOUND)
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from directory.models import Coop, CoopType
from directory.serializers import *
from directory.settings import EMAIL_HOST, EMAIL_PORT, SECRET_KEY

from django.contrib.auth.forms import PasswordResetForm
from pycountry import countries, subdivisions

@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'coops': reverse('coop-list', request=request, format=format),
        'coop_type': reverse('cooptypes-list', request=request, format=format),
        'users': reverse('user-list', request=request, format=format),
        'countries': reverse('country-list', request=request, format=format)
    })

# @api_view(["GET"])
# @permission_classes((IsAuthenticated,))
# def user_info(request):
#     return Response({
#         'user': request.user.username,
#         'expires_in': expires_in(request.auth)
#     }, status=HTTP_200_OK)

# def data(request):
#     # Create the HttpResponse object with the appropriate CSV header.
#     response = HttpResponse(content_type='text/csv')
#     response['Content-Disposition'] = 'attachment; filename="data.csv"'
#     writer = csv.writer(response, quoting=csv.QUOTE_ALL)
#     writer.writerow(['name','address','city','postal code','type','website','lon','lat'])
#     type = request.GET.get("type", "")
#     contains = request.GET.get("contains", "")
#     if type:
#         coops = Coop.objects.get_by_type(type)
#     elif contains:
#         coops = Coop.objects.contains_type(contains.split(","))
#     for coop in coops.order_by(Lower('name')):
#         for address in coop.addresses.all():
#             postal_code = address.locality.postal_code
#             city = address.locality.name + ", " + address.locality.state.code + " " + postal_code
#             coop_types = ', '.join([type.name for type in coop.types.all()])
#             if address.longitude and address.latitude:
#                 writer.writerow([coop.name, address.formatted, city, postal_code, coop_types, coop.web_site, address.longitude, address.latitude])
#     return response
    
class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    #TODO - Implement Owner Level Permissions

class CreateUserView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class CoopList(generics.ListCreateAPIView):
    serializer_class = CoopSerializer

    def perform_create(self, serializer):
        serializer.save(rec_updated_by=self.request.user)

    def get_queryset(self):
        queryset = Coop.objects.all()

        name = self.request.query_params.get('name', None)
        street = self.request.query_params.get('street', None)
        city = self.request.query_params.get('city', None)
        zip = self.request.query_params.get('zip', None)
        types_data = self.request.query_params.get('types', None)

        if name:
            queryset = queryset.filter(name__icontains=name)
        if street:
            queryset = queryset.filter(coop_address_tags__address__street_address__icontains=street).distinct()
        if city:
            queryset = queryset.filter(coop_address_tags__address__city__icontains=city).distinct()
        if zip:
            queryset = queryset.filter(coop_address_tags__address__postal_code__icontains=zip).distinct()
        if types_data:
            types = types_data.split(",")
            filter = Q(
                *[('types__name', type) for type in types],
                _connector=Q.OR
            )
            queryset = queryset.filter(filter)

        return queryset
    
    def get_permissions(self):
        if self.request.method == 'GET': #LIST
            self.permission_classes = [AllowAny]
        elif self.request.method == 'POST': #CREATE
            self.permission_classes = [IsAuthenticated]
        return [permission() for permission in self.permission_classes]

# class CoopListAll(APIView):
#     """
#     List all coops, or create a new coop. Includes details omitted in CoopList
#     """
#     def get(self, request, format=None):
#         contains = request.GET.get("contains", "")
#         if contains:
#             coops = Coop.objects.find(
#                 partial_name=contains,
#                 enabled=True
#             )
#         else:
#             partial_name = request.GET.get("name", "")
#             enabled_req_param = request.GET.get("enabled", None)
#             enabled = enabled_req_param.lower() == "true" if enabled_req_param else None
#             city = request.GET.get("city", None)
#             zip = request.GET.get("zip", None)
#             street = request.GET.get("street", None)
#             state = request.GET.get("state", None)
#             coop_types = request.GET.get("coop_type", None)
#             types_arr = coop_types.split(",") if coop_types else None

#             coops = Coop.objects.find(
#                 partial_name=partial_name,
#                 enabled=enabled,
#                 street=street,
#                 city=city,
#                 zip=zip,
#                 state_abbrev=state,
#                 types_arr=types_arr
#             )
#         serializer = CoopSpreadsheetSerializer(coops, many=True)
#         return Response(serializer.data)

#     def post(self, request, format=None):
#         serializer = CoopSpreadsheetSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CoopDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Coop.objects.all()
    serializer_class = CoopSerializer

    def perform_update(self, serializer):
        serializer.save(rec_updated_by=self.request.user)

    def get_permissions(self):
        if self.request.method == 'GET': #RETRIEVE
            self.permission_classes = [AllowAny]
        elif self.request.method in ['PUT', 'PATCH', 'DELETE']: #UPDATE (put, patch) DESTROY (delete)
            self.permission_classes = [IsAdminUser]
            #TODO - Implement owner level permssions 
        return [permission() for permission in self.permission_classes]

# class CoopDetail(APIView):
#     """
#     Retrieve, update or delete a coop instance.
#     """
#     def get_object(self, pk):
#         try:
#             return Coop.objects.get(pk=pk)
#         except Coop.DoesNotExist:
#             raise Http404
#
#     def patch(self, request, pk, format=None):
#         coop = self.get_object(pk)
#         serializer = CoopProposedChangeSerializer(coop, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class CoopsNoCoords(generics.ListAPIView):
    queryset = Coop.objects.exclude(coop_address_tags__isnull=True).prefetch_related(
        'coop_address_tags', 
        'coop_address_tags__address'
    ).filter(
        Q(coop_address_tags__address__latitude__isnull=True) | Q(coop_address_tags__address__longitude__isnull=True)
    )
    serializer_class = CoopSerializer
    permission_classes = [IsAdminUser]

class CoopsUnapproved(generics.ListAPIView):
    queryset = Coop.objects.filter(approved=False)
    serializer_class = CoopSerializer
    permission_classes = [IsAdminUser]

class PersonList(generics.ListAPIView):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    permission_classes = [AllowAny]
    
class PersonDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer

    def get_permissions(self):
        if self.request.method == 'GET': #RETRIEVE
            self.permission_classes = [AllowAny]
        elif self.request.method in ['PUT', 'PATCH', 'DELETE']: #UPDATE (put, patch) DESTROY (delete)
            self.permission_classes = [IsAdminUser]
            #TODO - Implement owner level permssions 
        return [permission() for permission in self.permission_classes]
    
class CoopTypeList(generics.ListAPIView):
    queryset = CoopType.objects.all().order_by(Lower('name'))
    serializer_class = CoopTypeSerializer
    permission_classes = [AllowAny]

class CoopTypeDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = CoopType.objects.all()
    serializer_class = CoopTypeSerializer

    def get_permissions(self):
        if self.request.method == 'GET': #RETRIEVE
            self.permission_classes = [AllowAny]
        elif self.request.method in ['PUT', 'PATCH', 'DELETE']: #UPDATE (put, patch) DESTROY (delete)
            self.permission_classes = [IsAdminUser]
        return [permission() for permission in self.permission_classes]
    
class CoopAddressTagsList(generics.ListAPIView):
    queryset = CoopAddressTags.objects.all()
    serializer_class = CoopAddressTagsSerializer
    permission_classes = [AllowAny]

class CoopAddressTagsDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = CoopAddressTags.objects.all()
    serializer_class = CoopAddressTagsSerializer

    def get_permissions(self):
        if self.request.method == 'GET': #RETRIEVE
            self.permission_classes = [AllowAny]
        elif self.request.method in ['PUT', 'PATCH', 'DELETE']: #UPDATE (put, patch) DESTROY (delete)
            self.permission_classes = [IsAdminUser]
            #TODO - Implement owner level permssions 
        return [permission() for permission in self.permission_classes]
    
class AddressList(generics.ListAPIView):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [AllowAny]

class AddressDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

    def get_permissions(self):
        if self.request.method == 'GET': #RETRIEVE
            self.permission_classes = [AllowAny]
        elif self.request.method in ['PUT', 'PATCH', 'DELETE']: #UPDATE (put, patch) DESTROY (delete)
            self.permission_classes = [IsAdminUser]
            #TODO - Implement owner level permssions 
        return [permission() for permission in self.permission_classes]
    
class ContactMethodList(generics.ListAPIView):
    queryset = ContactMethod.objects.all()
    serializer_class = ContactMethodSerializer
    permission_classes = [AllowAny]

class ContactMethodDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ContactMethod.objects.all()
    serializer_class = ContactMethodSerializer

    def get_permissions(self):
        if self.request.method == 'GET': #RETRIEVE
            self.permission_classes = [AllowAny]
        elif self.request.method in ['PUT', 'PATCH', 'DELETE']: #UPDATE (put, patch) DESTROY (delete)
            self.permission_classes = [IsAdminUser]
            #TODO - Implement owner level permssions 
        return [permission() for permission in self.permission_classes]

class CountryList(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):   
        countries_data = [
            {
                'code': 'US',
                'name': 'United States'
            }
        ]
        return Response(countries_data, status.HTTP_200_OK)
    
class StateList(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        input_country_code = self.kwargs['country_code']
        states_data = {'US': [{'name': 'Alaska', 'code': 'AK', 'country': 'US'}, {'name': 'Alabama', 'code': 'AL', 'country': 'US'}, {'name': 'Arkansas', 'code': 'AR', 'country': 'US'}, {'name': 'American Samoa', 'code': 'AS', 'country': 'US'}, {'name': 'Arizona', 'code': 'AZ', 'country': 'US'}, {'name': 'California', 'code': 'CA', 'country': 'US'}, {'name': 'Colorado', 'code': 'CO', 'country': 'US'}, {'name': 'Connecticut', 'code': 'CT', 'country': 'US'}, {'name': 'District of Columbia', 'code': 'DC', 'country': 'US'}, {'name': 'Delaware', 'code': 'DE', 'country': 'US'}, {'name': 'Florida', 'code': 'FL', 'country': 'US'}, {'name': 'Georgia', 'code': 'GA', 'country': 'US'}, {'name': 'Guam', 'code': 'GU', 'country': 'US'}, {'name': 'Hawaii', 'code': 'HI', 'country': 'US'}, {'name': 'Iowa', 'code': 'IA', 'country': 'US'}, {'name': 'Idaho', 'code': 'ID', 'country': 'US'}, {'name': 'Illinois', 'code': 'IL', 'country': 'US'}, {'name': 'Indiana', 'code': 'IN', 'country': 'US'}, {'name': 'Kansas', 'code': 'KS', 'country': 'US'}, {'name': 'Kentucky', 'code': 'KY', 'country': 'US'}, {'name': 'Louisiana', 'code': 'LA', 'country': 'US'}, {'name': 'Massachusetts', 'code': 'MA', 'country': 'US'}, {'name': 'Maryland', 'code': 'MD', 'country': 'US'}, {'name': 'Maine', 'code': 'ME', 'country': 'US'}, {'name': 'Michigan', 'code': 'MI', 'country': 'US'}, {'name': 'Minnesota', 'code': 'MN', 'country': 'US'}, {'name': 'Missouri', 'code': 'MO', 'country': 'US'}, {'name': 'Northern Mariana Islands', 'code': 'MP', 'country': 'US'}, {'name': 'Mississippi', 'code': 'MS', 'country': 'US'}, {'name': 'Montana', 'code': 'MT', 'country': 'US'}, {'name': 'North Carolina', 'code': 'NC', 'country': 'US'}, {'name': 'North Dakota', 'code': 'ND', 'country': 'US'}, {'name': 'Nebraska', 'code': 'NE', 'country': 'US'}, {'name': 'New Hampshire', 'code': 'NH', 'country': 'US'}, {'name': 'New Jersey', 'code': 'NJ', 'country': 'US'}, {'name': 'New Mexico', 'code': 'NM', 'country': 'US'}, {'name': 'Nevada', 'code': 'NV', 'country': 'US'}, {'name': 'New York', 'code': 'NY', 'country': 'US'}, {'name': 'Ohio', 'code': 'OH', 'country': 'US'}, {'name': 'Oklahoma', 'code': 'OK', 'country': 'US'}, {'name': 'Oregon', 'code': 'OR', 'country': 'US'}, {'name': 'Pennsylvania', 'code': 'PA', 'country': 'US'}, {'name': 'Puerto Rico', 'code': 'PR', 'country': 'US'}, {'name': 'Rhode Island', 'code': 'RI', 'country': 'US'}, {'name': 'South Carolina', 'code': 'SC', 'country': 'US'}, {'name': 'South Dakota', 'code': 'SD', 'country': 'US'}, {'name': 'Tennessee', 'code': 'TN', 'country': 'US'}, {'name': 'Texas', 'code': 'TX', 'country': 'US'}, {'name': 'United States Minor Outlying Islands', 'code': 'UM', 'country': 'US'}, {'name': 'Utah', 'code': 'UT', 'country': 'US'}, {'name': 'Virginia', 'code': 'VA', 'country': 'US'}, {'name': 'Virgin Islands', 'code': 'VI', 'country': 'US'}, {'name': 'Vermont', 'code': 'VT', 'country': 'US'}, {'name': 'Washington', 'code': 'WA', 'country': 'US'}, {'name': 'Wisconsin', 'code': 'WI', 'country': 'US'}, {'name': 'West Virginia', 'code': 'WV', 'country': 'US'}, {'name': 'Wyoming', 'code': 'WY', 'country': 'US'}]}
        if input_country_code in states_data:
            return Response(states_data[input_country_code], status.HTTP_200_OK)
        else:
            return Response("Country not found.", status.HTTP_404_NOT_FOUND)

# class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
#     reset_password_template_name = 'templates/users/password_reset.html'
#     email_template_name = 'users/password_reset_email.html'
#     subject_template_name = 'users/password_reset_subject'
#     success_message = "We've emailed you instructions for setting your password, " \
#                       "if an account exists with the email you entered. You should receive them shortly." \
#                       " If you don't receive an email, " \
#                       "please make sure you've entered the address you registered with, and check your spam folder."
#     success_url = reverse_lazy('users-home')

#     @method_decorator(csrf_exempt)
#     def dispatch(self, request, *args, **kwargs):
#         request.csrf_processing_done = True
#         return super().dispatch(request, *args, **kwargs)

#     def post(self, request, *args, **kwargs):
#         email = json.loads(request.body).get('username')
#         print("email: %s" % email)
#         #try:
#         if 1 > 0:
#             if User.objects.get(email=email).is_active:
#                 form = PasswordResetForm({'email': email})
#                 print("form valid? %s" % form.is_valid())
#                 if form.is_valid():
#                     request = HttpRequest()
#                     request.META['SERVER_NAME'] = socket.gethostbyname('localhost') #'127.0.0.1'
#                     request.META['SERVER_PORT'] = 8000
#                     # calling save() sends the email
#                     # check the form in the source code for the signature and defaults
#                     form.save(request=request,
#                         use_https=False,
#                         from_email="laredotornado@yahoo.com",
#                         email_template_name='../templates/users/password_reset_email.html')
#                 print("email: %s " % email)
#                 return super(ResetPasswordView, self).post(request, *args, **kwargs)
#         #except Exception as e:
#         #    print("\n\nerror ...\n\n")
#         #    print(e)
#         #    # this for if the email is not in the db of the system
#         #    return super(ResetPasswordView, self).post(request, *args, **kwargs)
