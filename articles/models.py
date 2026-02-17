import os
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator
from utils.models import BaseModel
from utils.helpers import calculate_file_hash

class Category(BaseModel):
    name = models.CharField(max_length=100, verbose_name="Kategoriya nomi")
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Kategoriyalar"

class Article(BaseModel):
    STATUS_CHOICES = [
        ('draft', 'Qoralama'),
        ('submitted', 'Yuborilgan (Moderatsiyada)'),
        ('changes_requested', 'Tahrir talab etiladi'),
        ('rejected', 'Rad etilgan'),
        ('published', 'Chop etilgan'),
    ]

    title = models.CharField(max_length=500, verbose_name="Sarlavha")
    slug = models.SlugField(max_length=500, unique=True, blank=True)
    
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='articles')
    submitter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submitted_articles')
    
    # Asosiy ma'lumotlar
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True, verbose_name="Muqova rasmi")
    abstract = models.TextField(verbose_name="Annotatsiya")
    is_resubmission = models.BooleanField(default=False)
    
    # ASOSIY FAYL (Faqat PDF yoki Word)
    original_file = models.FileField(
        upload_to='articles/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])],
        verbose_name="Maqola fayli"
    )
    file_hash = models.CharField(max_length=64, blank=True, unique=True, verbose_name="Fayl Xeshi")
    
    # Metadata
    keywords = models.CharField(max_length=255, help_text="Vergul bilan ajratilgan")
    references = models.TextField(blank=True, null=True, verbose_name="Adabiyotlar ro'yxati")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    views = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        # Agar slug bo'sh bo'lsa, sarlavhadan yasaymiz
        if not self.slug:
            base_slug = slugify(self.title)
            # Dublikat bo'lmasligi uchun tekshiramiz
            unique_slug = base_slug
            num = 1
            while Article.objects.filter(slug=unique_slug).exists():
                unique_slug = f'{base_slug}-{num}'
                num += 1
            self.slug = unique_slug
            
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def file_extension(self):
        name, extension = os.path.splitext(self.original_file.name)
        return extension.lower()

# ArticleAuthor modeli o'zgarishsiz
class ArticleAuthor(BaseModel):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='authors')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=255, blank=True, verbose_name="F.I.SH")
    affiliation = models.CharField(max_length=255, blank=True, verbose_name="Ish joyi")
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.full_name or str(self.user)