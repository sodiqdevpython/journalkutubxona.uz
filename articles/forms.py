from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from .models import Article, ArticleAuthor

class ArticleForm(forms.ModelForm):
    # Modelda bo'lmagan, lekin forma uchun kerakli maydon (Rozilik)
    terms_accepted = forms.BooleanField(
        required=True,
        label="Men barcha qoidalarga roziman",
        help_text="Maqola o'zimniki ekanligini, undagi ma'lumotlar to'g'riligini va plagiat yo'qligini tasdiqlayman."
    )

    class Meta:
        model = Article
        fields = ['title', 'category', 'abstract', 'keywords', 'references', 'cover_image', 'original_file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Maqola mavzusi'}),
            'category': forms.Select(attrs={'class': 'form-control form-select'}),
            'abstract': forms.Textarea(attrs={'class': 'form-control', 'rows': 15, 'placeholder': 'Qisqacha mazmuni...'}),
            'keywords': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vergul bilan ajratilgan (Masalan: AI, Security)'}),
            'references': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'original_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
        }

    def clean_original_file(self):
        file = self.cleaned_data.get('original_file')
        if file:
            # 1. Hajmni tekshirish (30MB)
            limit_mb = 30
            if file.size > limit_mb * 1024 * 1024:
                raise ValidationError(f"Fayl hajmi {limit_mb}MB dan oshmasligi kerak!")
            
            # 2. Formatni tekshirish (Qo'shimcha himoya)
            ext = file.name.split('.')[-1].lower()
            if ext not in ['pdf', 'doc', 'docx']:
                raise ValidationError("Faqat PDF, DOC yoki DOCX fayllar qabul qilinadi.")
        return file

class ArticleAuthorForm(forms.ModelForm):
    # Bu checkbox html da JS orqali inputlarni almashtirish uchun ishlatiladi
    is_manual = forms.BooleanField(required=False, label="Ro'yxatda yo'qmi?", widget=forms.CheckboxInput(attrs={'class': 'manual-toggle'}))

    class Meta:
        model = ArticleAuthor
        fields = ['user', 'full_name', 'affiliation', 'order']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control user-select'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control manual-input', 'placeholder': 'F.I.SH'}),
            'affiliation': forms.TextInput(attrs={'class': 'form-control manual-input', 'placeholder': 'Ish joyi'}),
            'order': forms.HiddenInput(), # Tartib raqami avtomatik qo'yiladi
        }

ArticleAuthorFormSet = inlineformset_factory(
    Article, ArticleAuthor,
    form=ArticleAuthorForm,
    extra=0,       # Default holatda 0 ta (faqat o'zi bo'ladi, keyin qo'shadi)
    min_num=0,
    max_num=20,    # Maksimum 20 ta muallif
    can_delete=True
)