from django.contrib import admin
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Register your models here.


class CustomUserAdmin(UserAdmin):
    # This adds the 'role' field to the User edit page in the Admin panel
    fieldsets = UserAdmin.fieldsets + (
        ('Role Management', {'fields': ('role',)}),
    )
    list_display = ['username', 'email', 'role', 'is_staff']


admin.site.register(User, CustomUserAdmin)
