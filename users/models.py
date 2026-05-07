from django.db import models
from django.contrib.auth.models import AbstractUser
from utils.models import BaseModel

class CustomUser(AbstractUser, BaseModel):
    bio = models.TextField(blank=True, null=True, verbose_name="Biografiya")
    institution = models.CharField(max_length=255, blank=True, null=True, verbose_name="Ish/O'qish joyi")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Avatar")
    
    phone_number = models.CharField(max_length=20, verbose_name="Telefon raqam")
    telegram_username = models.CharField(max_length=50, blank=True, null=True, verbose_name="Telegram (@siz)")
    
    show_phone = models.BooleanField(default=False, verbose_name="Telefon raqam ko'rinsinmi?")
    show_email = models.BooleanField(default=False, verbose_name="Email ko'rinsinmi?")
    
    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"