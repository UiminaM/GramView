from django import forms
from main.models import Review
from django.contrib.auth.forms import UserChangeForm
from main.models import CustomUser
from .models import Channels


class ProfileEditForm(UserChangeForm):
    email = forms.EmailField(required=True)
    username = forms.CharField(max_length=150, required=True)
    profile_picture = forms.ImageField(required=False)
    password = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'profile_picture']


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['text', 'rating']

class BaseChannelForm(forms.ModelForm):
    class Meta:
        model = Channels
        fields = ['username']


class AdvanceChannelForm(forms.ModelForm):
    phone_number = forms.CharField(max_length=20, required=True)
    verification_code = forms.CharField(max_length=6, required=True)

    class Meta:
        model = Channels
        fields = ['username']