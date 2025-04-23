from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView



urlpatterns = [
    path('channels/', views.channels_view, name='channels'),
    path('posts/', views.posts_view, name='posts'),
    path('my-channels/', views.my_channels_view, name='my_channels'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='edit_profile'),
    path('logout/', LogoutView.as_view(), name='logout'),
]