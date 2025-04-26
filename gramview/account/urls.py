from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path('channels/', views.channels, name='channels'),
    path('channels/add/', views.add_channel, name='add_channel'),
    path('channels/delete/<int:channel_id>/', views.delete_channel, name='delete_channel'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='edit_profile'),
    path('logout/', LogoutView.as_view(), name='logout'),
]