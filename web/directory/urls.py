from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from directory import settings, views
from directory.models import Coop
from directory.serializers import CoopSerializer
from rest_framework.authtoken.views import obtain_auth_token
from django.contrib.auth import views as auth_views

urlpatterns = format_suffix_patterns([
    path('', views.api_root),
    # path('data', views.data, name='data'),
    path('coops/', views.CoopList.as_view(), name='coop-list'),
    path('coops/<int:pk>/', views.CoopDetail.as_view(), name='coop-detail'),
    path('coops/no_coords', views.CoopsNoCoords.as_view(), name='coops_wo_coordinates'),
    path('coops/unapproved', views.CoopsUnapproved.as_view(), name='unapproved_coops'),
    path('coops/all/', views.CoopList.as_view()),
    path('people/', views.PersonList.as_view(), name='person-list'),
    path('people/<int:pk>/', views.PersonDetail.as_view(), name='person-detail'),
    path('users/', views.UserList.as_view(), name='user-list'),
    path('users/<int:pk>/', views.UserDetail.as_view(), name='user-detail'),
    path('predefined_types/', views.CoopTypeList.as_view()),
    path('coop_types/', views.CoopTypeList.as_view(), name='coop-type-list'),
    path('coop_types/<int:pk>/', views.CoopTypeDetail.as_view(), name='coop-type-detail'),
    path('countries/', views.CountryList.as_view(), name='country-list'),        
    path('states/<country_code>', views.StateList.as_view(), name='state-list'),
    #     path('login', views.signin),
    #     path(settings.LOGOUT_PATH, views.signout),
    #     path('user_info', views.user_info),
    #     path('reset_password', views.ResetPasswordView.as_view(template_name='../templates/users/password_reset.html'), name='reset_password'),
    #     path('password-reset-confirm/<uidb64>/<token>/',
    #          auth_views.PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html'),
    #          name='password_reset_confirm'),
    #     path('password-reset-complete/',
    #          auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'),
    #          name='password_reset_complete'),
])