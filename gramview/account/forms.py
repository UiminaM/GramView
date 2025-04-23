from django import forms
from main.models import Review
from django.contrib.auth.forms import UserChangeForm
from main.models import CustomUser


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
