from django.contrib import admin
from django.contrib.auth.models import Permission

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = "pk", "user", "bio", "agreement_accepted"
    list_display_links = "pk", "user"

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = "pk", "name", "codename", "content_type"
    list_filter = "content_type",
    search_fields = "name", "codename"