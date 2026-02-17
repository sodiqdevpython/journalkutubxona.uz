from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser
from django.contrib.auth import get_user_model

User = get_user_model()

# --- RO'YXATDAN O'TISH FORMASI ---
class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'institution']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. Maydon nomlarini O'zbekcha qilish
        self.fields['username'].label = "Foydalanuvchi nomi (Login)"
        self.fields['username'].help_text = "Lotin harflari, raqamlar va _ belgisidan foydalaning."
        
        self.fields['first_name'].label = "Ismingiz"
        self.fields['first_name'].required = True # Ism majburiy bo'lsin
        
        self.fields['last_name'].label = "Familiyangiz"
        self.fields['last_name'].required = True
        
        self.fields['email'].label = "Email manzili"
        self.fields['email'].required = True
        
        self.fields['phone_number'].label = "Telefon raqamingiz"
        self.fields['institution'].label = "Ish yoki o'qish joyingiz"

        # Parol maydonlari (UserCreationForm dan keladi)
        # Eslatma: 'password' maydonlari modelda yo'q, ular forma ichida generatsiya qilinadi
        if 'key1' in self.fields: # Ba'zi versiyalarda farq qilishi mumkin, lekin odatda pastdagi ishlaydi
             pass

        # 2. Inputlarga Bootstrap class va Placeholder qo'shish
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            

# --- KIRISH (LOGIN) FORMASI ---
class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['username'].label = "Login"
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Login'})
        
        self.fields['password'].label = "Parol"
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Parolingiz'})
    

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'avatar', 'first_name', 'last_name', 'email', 
            'bio', 'institution', 
            'phone_number', 'telegram_username', 
            'show_phone', 'show_email'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ismingiz'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Familiyangiz'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'institution': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+998 90 123 45 67'}),
            'telegram_username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '@username'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'O\'zingiz haqingizda qisqacha...'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control-file'}),
        }
        labels = {
            'avatar': 'Profil rasmi (Avatar)',
        }