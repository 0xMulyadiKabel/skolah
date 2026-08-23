from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import School, User


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("nama", "jam_masuk", "jam_pulang", "toleransi_keterlambatan_menit")
    search_fields = ("nama",)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "role", "school", "is_staff")
    list_filter = ("role", "school")

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Info Tambahan", {"fields": ("role", "school")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Info Tambahan", {"fields": ("role", "school")}),
    )