from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    profile_picture = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.jpg', blank=True)
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_groups',  # Это имя будет использоваться для обратной связи с Group
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_permissions',  # Это имя будет использоваться для обратной связи с Permission
        blank=True
    )


class Service(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    is_displayed = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Review(models.Model):
    id_profile = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_create = models.DateField(auto_now_add=True)
    text = models.TextField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])

    def __str__(self):
        return f"Review by {self.id_profile.username} - Rating: {self.rating}"

