import csv
import json
import socket

from address.models import Country, Locality, State
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.db.models.functions import Lower
from django.http import Http404, HttpResponse
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, mixins, generics, permissions, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import CreateAPIView
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.status import (HTTP_200_OK, HTTP_400_BAD_REQUEST,
                                   HTTP_404_NOT_FOUND)
from rest_framework.views import APIView
from django.utils.decorators import method_decorator

from directory.authentication import expires_in
from directory.models import Coop, CoopType
from directory.serializers import *
from directory.settings import EMAIL_HOST, EMAIL_PORT, SECRET_KEY

from .authentication import expires_in, token_expire_handler
from .serializers import UserSigninSerializer
from django.contrib.auth.forms import PasswordResetForm
from django.http import HttpRequest

@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'coops': reverse('coop-list', request=request, format=format),
        'coop_type': reverse('coop-type-list', request=request, format=format),
        'users': reverse('user-list', request=request, format=format),
        'countries': reverse('country-list', request=request, format=format)
    })

# @api_view(["POST"])
# @permission_classes((AllowAny,))  # here we specify permission by default we set IsAuthenticated
# def signin(request):
#     signin_serializer = UserSigninSerializer(data = request.data)
#     if not signin_serializer.is_valid():
#         return Response(signin_serializer.errors, status = HTTP_400_BAD_REQUEST)

#     user = authenticate(
#             username = signin_serializer.data['username'],
#             password = signin_serializer.data['password'] 
#         )
    
#     if not user:
#         return Response({'detail': 'Invalid Credentials or activate account'}, status=HTTP_404_NOT_FOUND)
        
#     #TOKEN STUFF
#     token, _ = Token.objects.get_or_create(user = user)
    
#     #token_expire_handler will check, if the token is expired it will generate new one
#     is_expired, token = token_expire_handler(token)     # The implementation will be described further
#     user_serialized = UserSerializer(user)

#     return Response({
#         'user': user_serialized.data, 
#         'expires_in': expires_in(token),
#         'token': token.key
#     }, status=HTTP_200_OK)

# @api_view(["GET"])
# @permission_classes((IsAuthenticated,))
# def signout(request):
#     user = request.user
#     print("user: %s" % user)
#     Token.objects.filter(user=user).delete() 
#     # Remove header
#     return Response({}, status=HTTP_200_OK)


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
    
class CoopsNoCoords(generics.ListAPIView):
    queryset = Coop.objects.exclude(coop_address_tags__isnull=True).prefetch_related(
        'coop_address_tags', 
        'coop_address_tags__address'
    ).filter(
        Q(coop_address_tags__address__latitude__isnull=True) | Q(coop_address_tags__address__longitude__isnull=True)
    )
    serializer_class = CoopSerializer

class CoopsUnapproved(generics.ListAPIView):
    queryset = Coop.objects.filter(approved=False)
    serializer_class = CoopSerializer

class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


# class CreateUserView(CreateAPIView):

#     model = User
#     permission_classes = [
#         IsAuthenticated
#     ]
#     serializer_class = UserSerializer
    
class CoopList(generics.ListCreateAPIView):
    queryset = Coop.objects.all()
    serializer_class = CoopSerializer
    permission_classes = [ IsAuthenticated ]

    def perform_create(self, serializer):
        serializer.save(rec_updated_by=self.request.user)

# class CoopList(APIView):
#     """
#     List all coops, or create a new coop.
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
#         serializer = CoopSearchSerializer(coops, many=True)
#         return Response(serializer.data)

#     def post(self, request, format=None):
#         serializer = CoopSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_update(self, serializer):
        serializer.save(rec_updated_by=self.request.user)

# class CoopDetail(APIView):
#     """
#     Retrieve, update or delete a coop instance.
#     """
#     def get_object(self, pk):
#         try:
#             return Coop.objects.get(pk=pk)
#         except Coop.DoesNotExist:
#             raise Http404

#     def get(self, request, pk, format=None):
#         coop = self.get_object(pk)
#         serializer = CoopSerializer(coop)
#         return Response(serializer.data)

#     def put(self, request, pk, format=None):
#         coop = self.get_object(pk)
#         serializer = CoopSerializer(coop, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def patch(self, request, pk, format=None):
#         coop = self.get_object(pk)
#         serializer = CoopProposedChangeSerializer(coop, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, pk, format=None):
#         coop = self.get_object(pk)
#         coop.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)

# class CoopWithPerson(APIView):
#     """
#     Retrieve, update or delete a coop instance.
#     """
#     def get_object(self, pk):
#         try:
#             return Coop.objects.get(pk=pk)
#         except Coop.DoesNotExist:
#             raise Http404

#     def get(self, request, pk, format=None):
#         coop = self.get_object(pk)
#         serializer = CoopSerializerWithPerson(coop)
#         return Response(serializer.data)

#     def put(self, request, pk, format=None):
#         coop = self.get_object(pk)
#         serializer = CoopSerializerWithPerson(coop, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def patch(self, request, pk, format=None):
#         coop = self.get_object(pk)
#         serializer = CoopProposedChangeSerializer(coop, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, pk, format=None):
#         coop = self.get_object(pk)
#         coop.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)

class PersonList(generics.ListCreateAPIView):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer

# class PersonList(APIView):
#     """
#     List all people, or create a new person.
#     """
#     def get(self, request, format=None):
#         coop = request.GET.get("coop", "")
#         if coop:
#             people = Person.objects.filter(coops__in=[coop])
#         else:
#             people = Person.objects.all()
#         serializer = PersonSerializer(people, many=True)
#         return Response(serializer.data)

#     def post(self, request, format=None):
#         serializer = PersonSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class PersonWithCoopList(APIView):
#     """
#     List all people, or create a new person.
#     """
#     def get(self, request, format=None):
#         coop = request.GET.get("coop", "")
#         if coop:
#             people = Person.objects.filter(coops__in=[coop])
#         else:
#             people = Person.objects.all()
#         serializer = PersonWithCoopSerializer(people, many=True)
#         return Response(serializer.data)

#     def post(self, request, format=None):
#         serializer = PersonWithCoopSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PersonDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

# class PersonDetail(APIView):
#     """
#     Retrieve, update or delete a person instance.
#     """
#     def get_object(self, pk):
#         try:
#             return Person.objects.get(pk=pk)
#         except Coop.DoesNotExist:
#             raise Http404

#     def get(self, request, pk, format=None):
#         person = self.get_object(pk)
#         serializer = PersonSerializer(person)
#         return Response(serializer.data)

#     def put(self, request, pk, format=None):
#         person = self.get_object(pk)
#         serializer = PersonSerializer(person, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, pk, format=None):
#         person = self.get_object(pk)
#         person.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)

class CoopTypeList(generics.ListAPIView):
    queryset = CoopType.objects.all().order_by(Lower('name'))
    serializer_class = CoopTypeSerializer

class CoopTypeDetail(generics.RetrieveAPIView):
    queryset = CoopType.objects.all()
    serializer_class = CoopTypeSerializer

class CountryList(generics.ListAPIView):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    
class StateList(generics.ListAPIView):
    serializer_class = StateSerializer

    def get_queryset(self):
        queryset = State.objects.all()
        country_code = self.kwargs['country_code']
        queryset = queryset.filter(country__code=country_code)
        return queryset


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
