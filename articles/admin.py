from django.contrib import admin
from .models import Article, ArticleAuthor, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

class ArticleAuthorInline(admin.TabularInline):
    model = ArticleAuthor
    extra = 1
    fields = ('user', 'full_name', 'affiliation', 'order')
    autocomplete_fields = ['user'] 

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    inlines = [ArticleAuthorInline] 
    
    list_display = ('title', 'submitter', 'category', 'status', 'views', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('title', 'abstract', 'submitter__username', 'keywords')
    
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('views', 'file_hash', 'created_at', 'updated_at')
    
    actions = ['make_published', 'make_rejected']

    def make_published(self, request, queryset):
        queryset.update(status='published')
    make_published.short_description = "Tanlangan maqolalarni 'Chop etilgan' qilish"

    def make_rejected(self, request, queryset):
        queryset.update(status='rejected')
    make_rejected.short_description = "Tanlangan maqolalarni 'Rad etilgan' qilish"