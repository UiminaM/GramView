from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import Service, Review

User = get_user_model()

admin.site.register(Service)
admin.site.register(Review)
admin.site.register(User, UserAdmin)
