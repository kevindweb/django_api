from django.contrib import admin
from .models import Dog, User
from django.contrib.auth.admin import UserAdmin

@admin.register(Dog)
class DogAdmin(admin.ModelAdmin):
    list_display = ["name", "breed", "favorite_activity"]

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ["username", "api_token"]
