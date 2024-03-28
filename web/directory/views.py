from django.core.mail import send_mail
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, generics
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from directory.models import ContactMethod, CoopType, Address, AddressCache, CoopAddressTags, CoopPublic, Coop, CoopProposal, Person
from directory.serializers import *

@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'coops': reverse('coop-list', request=request, format=format),
        'coop_type': reverse('cooptype-list', request=request, format=format),
        'users': reverse('user-list', request=request, format=format),
        'countries': reverse('country-list', request=request, format=format)
    })

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
    
class CoopList(generics.ListAPIView):
    serializer_class = CoopXSerializer

    def perform_create(self, serializer):
        serializer.save(rec_updated_by=self.request.user)

    def get_queryset(self):
        queryset = Coop.objects.filter(status=Coop.Status.ACTIVE)

        is_public = self.request.GET.get("is_public", None)
        if is_public is not None:
            is_public = is_public.lower() == "true"
        name = self.request.query_params.get('name', None)
        street = self.request.query_params.get('street', None)
        city = self.request.query_params.get('city', None)
        zip = self.request.query_params.get('zip', None)
        types_data = self.request.query_params.get('types', None)

        #TODO- if address.is_public=False, should we be showing it in results?

        if is_public is not None:
            queryset = queryset.filter(is_public=is_public)
        if name:
            queryset = queryset.filter(name__icontains=name)
        if street:
            queryset = queryset.filter(addresses__address__street_address__icontains=street).distinct()
        if city:
            queryset = queryset.filter(addresses__address__city__icontains=city).distinct()
        if zip:
            queryset = queryset.filter(addresses__address__postal_code__icontains=zip).distinct()
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

class CoopDetail(generics.RetrieveAPIView):
    queryset = Coop.objects.filter(status=Coop.Status.ACTIVE)
    serializer_class = CoopXSerializer
    permission_classes = [AllowAny]
        
class CoopsNoCoords(generics.ListAPIView):
    queryset = Coop.objects.filter(status=Coop.Status.ACTIVE).exclude(addresses__isnull=True).filter(
            Q(addresses__address__latitude__isnull=True) | Q(addresses__address__longitude__isnull=True)
        )
    serializer_class = CoopXSerializer
    permission_classes = [IsAdminUser]

class CoopsUnapproved(generics.ListAPIView):
    queryset = CoopProposal.objects.filter(proposal_status=CoopProposal.ProposalStatus.PENDING)
    serializer_class = CoopXSerializer
    permission_classes = [IsAdminUser]

class PersonList(generics.ListAPIView):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    permission_classes = [AllowAny]
    
class PersonDetail(generics.RetrieveAPIView):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    permission_classes = [AllowAny]
    
class CoopTypeList(generics.ListAPIView):
    queryset = CoopType.objects.all().order_by(Lower('name'))
    serializer_class = CoopTypeSerializer
    permission_classes = [AllowAny]

class CoopTypeDetail(generics.RetrieveAPIView):
    queryset = CoopType.objects.all()
    serializer_class = CoopTypeSerializer
    permission_classes = [AllowAny]
    
class CoopAddressTagsList(generics.ListAPIView):
    queryset = CoopAddressTags.objects.all()
    serializer_class = CoopAddressTagsSerializer
    permission_classes = [AllowAny]

class CoopAddressTagsDetail(generics.RetrieveAPIView):
    queryset = CoopAddressTags.objects.all()
    serializer_class = CoopAddressTagsSerializer
    permission_classes = [AllowAny]
    
class AddressList(generics.ListAPIView):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [AllowAny]

class AddressDetail(generics.RetrieveAPIView):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [AllowAny]
    
class ContactMethodList(generics.ListAPIView):
    queryset = ContactMethod.objects.all()
    serializer_class = ContactMethodSerializer
    permission_classes = [AllowAny]

class ContactMethodDetail(generics.RetrieveAPIView):
    queryset = ContactMethod.objects.all()
    serializer_class = ContactMethodSerializer
    permission_classes = [AllowAny]

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
        
class PasswordResetRequestView(APIView):
    def post(self, request):
        email = request.data.get("email")
        user = User.objects.filter(email=email).first()
        if user:
            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            link = request.build_absolute_uri(reverse('password-reset-confirm', args=[uid, token]))
            send_mail(
                "Password Reset Request",
                f'Please go to the following link to reset your password: {link}',
                'from@example.com',
                [email],
                fail_silently=False,
            )
            return Response({"message": "Password reset link has been sent to your email."}, status=status.HTTP_200_OK)
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

class PasswordResetConfirmView(APIView):
    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except:
            user = None
        token_generator = PasswordResetTokenGenerator()
        if user is not None and token_generator.check_token(user, token):
            new_password = request.data.get("password")
            user.set_password(new_password)
            user.save()
            return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid token or user ID."}, status=status.HTTP_400_BAD_REQUEST)
    
#============================================================================
    
class CoopPublicList(generics.ListAPIView):
    queryset = CoopPublic.objects.all()
    serializer_class = CoopPublicListSerializer
    permission_classes = [AllowAny]

class CoopProposalList(generics.ListAPIView):
    queryset = CoopProposal.objects.all()
    serializer_class = CoopProposalListSerializer
    permission_classes = [IsAdminUser]

class CoopProposalRetrieve(generics.RetrieveAPIView):
    queryset = CoopProposal.objects.all()
    serializer_class = CoopProposalRetrieveSerializer
    permission_classes = [IsAdminUser]
    
class CoopProposalCreate(generics.CreateAPIView):
    serializer_class = CoopProposalCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user)

class CoopProposalReview(generics.UpdateAPIView):
    queryset = CoopProposal.objects.all()
    serializer_class = CoopProposalReviewSerializer
    permission_classes = [IsAdminUser]

    def perform_update(self, serializer):
        serializer.save(reviewed_by=self.request.user)