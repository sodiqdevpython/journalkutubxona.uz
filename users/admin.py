from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'institution', 'phone_number', 'is_staff')
    
    search_fields = ('username', 'first_name', 'last_name', 'email', 'institution')
    
    list_filter = ('is_staff', 'is_superuser', 'institution', 'groups')

    fieldsets = UserAdmin.fieldsets + (
        ('Qo\'shimcha ma\'lumotlar', {
            'fields': ('bio', 'institution', 'avatar', 'phone_number', 'telegram_username')
        }),
        ('Maxfiylik sozlamalari', {
            'fields': ('show_phone', 'show_email')
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)