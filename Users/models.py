from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class User(AbstractUser):
    # Role Based Choices
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('accountant', 'Accountant'),
        ('bookkeeper', 'Bookkeeper'),
        ('client', 'Client'),
    )

    role = models.CharField(
        max_length=10, choices=ROLE_CHOICES, default='client')

    # Good Name Function
    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"
