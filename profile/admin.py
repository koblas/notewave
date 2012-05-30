from django.contrib import admin
from .models import UserProfile

class ProfileAdmin(admin.ModelAdmin) :
    fields = ['data', 'image', 'username', 'balance']

admin.site.register(UserProfile, ProfileAdmin) 
