from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy

class CustomLoginView(LoginView):
    template_name = 'auth/authorization.html'

    def get_success_url(self):
        return reverse_lazy('profile')

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            base_group, created = Group.objects.get_or_create(name='base')
            user.groups.add(base_group)
        return user
