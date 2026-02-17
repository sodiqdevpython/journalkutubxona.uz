from django import forms
from .models import Comment, Message
from users.models import CustomUser

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Fikringizni qoldiring...'
            }),
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body']
        widgets = {
            'recipient': forms.Select(attrs={'class': 'form-control form-select'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mavzu'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Xabar yuborishda o'zidan boshqa hamma userlarni chiqarish (ixtiyoriy logika)
        # Agar kerak bo'lsa, querysetni shu yerda filtrlash mumkin

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text'] # Modelda 'message' yoki 'body' bo'lsa shunga o'zgartiring
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Fikringizni yozing...'
            })
        }

