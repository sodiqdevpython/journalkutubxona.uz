from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    # Admin panelda ko'rinadigan ustunlar
    list_display = ('username', 'email', 'first_name', 'last_name', 'institution', 'phone_number', 'is_staff')
    
    # Qidiruv maydonlari
    search_fields = ('username', 'first_name', 'last_name', 'email', 'institution')
    
    # Filtrlash (o'ng tomonda)
    list_filter = ('is_staff', 'is_superuser', 'institution', 'groups')

    # Foydalanuvchini tahrirlash sahifasidagi maydonlar guruhi
    fieldsets = UserAdmin.fieldsets + (
        ('Qo\'shimcha ma\'lumotlar', {
            'fields': ('bio', 'institution', 'avatar', 'phone_number', 'telegram_username')
        }),
        ('Maxfiylik sozlamalari', {
            'fields': ('show_phone', 'show_email')
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)