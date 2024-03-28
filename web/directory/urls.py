from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from directory import views
from django.contrib import admin
from django.contrib.auth import views as auth_views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = format_suffix_patterns([
    path('', views.api_root),
    # path('data', views.data, name='data'),
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/', views.UserList.as_view(), name='user-list'),
    path('users/<int:pk>/', views.UserDetail.as_view(), name='user-detail'),
    path('register/', views.CreateUserView.as_view(), name='register'),
    path('password_reset/', views.PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset-confirm/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),

    path('coops/', views.CoopList.as_view(), name='coop-list'),
    path('coops/<int:pk>/', views.CoopDetail.as_view(), name='coop-detail'),
    path('coops/no_coords', views.CoopsNoCoords.as_view(), name='coop-no-coords'),
    path('coops/unapproved', views.CoopsUnapproved.as_view(), name='coop-unapproved'),
    path('coops/public/', views.CoopPublicList.as_view(), name='coop-public'),
    path('coops/proposal/', views.CoopProposalList.as_view(), name='coop-proposal-list'),
    path('coops/proposal/<int:pk>/', views.CoopProposalRetrieve.as_view(), name='coop-proposal-list'),
    path('coops/proposal/create/', views.CoopProposalCreate.as_view(), name='coop-proposal'),
    path('coops/proposal/review/<int:pk>/', views.CoopProposalReview.as_view(), name='coop-review'),

    path('people/', views.PersonList.as_view(), name='person-list'),
    path('people/<int:pk>/', views.PersonDetail.as_view(), name='person-detail'),
    path('predefined_types/', views.CoopTypeList.as_view()),
    path('coop_types/', views.CoopTypeList.as_view(), name='cooptype-list'),
    path('coop_types/<int:pk>/', views.CoopTypeDetail.as_view(), name='cooptype-detail'),
    path('coopaddresstags/', views.CoopAddressTagsList.as_view(), name='coopaddresstags-list'),
    path('coopaddresstags/<int:pk>/', views.CoopAddressTagsDetail.as_view(), name='coopaddresstags-detail'),
    path('addresses/', views.AddressList.as_view(), name='address-list'),
    path('addresses/<int:pk>/', views.AddressDetail.as_view(), name='address-detail'),  
    path('contactmethods/', views.ContactMethodList.as_view(), name='contactmethod-list'),
    path('contactmethods/<int:pk>/', views.ContactMethodDetail.as_view(), name='contactmethod-detail'),  
    path('countries/', views.CountryList.as_view(), name='country-list'),        
    path('states/<country_code>', views.StateList.as_view(), name='state-list'),



    #     path('user_info', views.user_info),
])