from django.contrib import admin
from .models import Article, ArticleAuthor, Category

# 1. Kategoriya Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)} # Nom yozganda slug avtomatik yoziladi
    search_fields = ('name',)

# 2. Mualliflar uchun Inline (Maqola ichida chiqadi)
class ArticleAuthorInline(admin.TabularInline):
    model = ArticleAuthor
    extra = 1 # Bitta bo'sh qator ko'rsatib turadi
    fields = ('user', 'full_name', 'affiliation', 'order')
    autocomplete_fields = ['user'] # Userlarni qidirib topish uchun (drop-down emas)

# 3. Maqola Admin
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    inlines = [ArticleAuthorInline] # Mualliflarni ulash
    
    list_display = ('title', 'submitter', 'category', 'status', 'views', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('title', 'abstract', 'submitter__username', 'keywords')
    
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('views', 'file_hash', 'created_at', 'updated_at')
    
    # Admin panelda "Action" qo'shish (Masalan: Tanlanganlarni chop etish)
    actions = ['make_published', 'make_rejected']

    def make_published(self, request, queryset):
        queryset.update(status='published')
    make_published.short_description = "Tanlangan maqolalarni 'Chop etilgan' qilish"

    def make_rejected(self, request, queryset):
        queryset.update(status='rejected')
    make_rejected.short_description = "Tanlangan maqolalarni 'Rad etilgan' qilish"