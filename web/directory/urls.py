from django.urls import path
from directory import views
from django.contrib import admin
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


urlpatterns = [

    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/admin/', admin.site.urls),

    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    path('api/v1/users/<int:pk>/', views.UserDetail.as_view(), name='user-detail'),
    path('api/v1/register/', views.UserRegister.as_view(), name='register'),

    path('api/v1/password-reset/', views.PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('api/v1/password-reset-confirm/<str:uidb64>/<str:token>/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),

    path('api/v1/coops/', views.CoopList.as_view(), name='coop-list'),
    path('api/v1/coops/<int:coop_public_id>/', views.CoopDetail.as_view(), name='coop-detail'),
    path('api/v1/coops/no_coords', views.CoopsNoCoords.as_view(), name='coop-no-coords'),
    path('api/v1/coops/unapproved', views.CoopsUnapproved.as_view(), name='coop-unapproved'),
    path('api/v1/coops/csv/', views.CoopCSVView.as_view(), name='data'),
    
    path('api/v1/coops/proposal/', views.CoopProposalList.as_view(), name='coop-proposal-list'),
    path('api/v1/coops/proposal/<int:pk>/', views.CoopProposalRetrieve.as_view(), name='coop-proposal-list'),
    path('api/v1/coops/proposal/create/', views.CoopProposalCreate.as_view(), name='coop-proposal'),
    path('api/v1/coops/proposal/review/<int:pk>/', views.CoopProposalReview.as_view(), name='coop-review'),

    path('api/v1/predefined_types/', views.CoopTypeList.as_view()),
    path('api/v1/coop_types/', views.CoopTypeList.as_view(), name='cooptype-list'),
    path('api/v1/coop_types/<int:pk>/', views.CoopTypeDetail.as_view(), name='cooptype-detail'),
    path('api/v1/countries/', views.CountryList.as_view(), name='country-list'),        
    path('api/v1/states/<str:country_code>', views.StateList.as_view(), name='state-list'),
]