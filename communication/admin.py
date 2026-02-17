from django.contrib import admin
from .models import Message, Comment

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender', 'recipient', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('subject', 'body', 'sender__username', 'recipient__username')
    readonly_fields = ('created_at',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('article', 'user', 'short_text', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('text', 'user__username', 'article__title')

    # Matn uzun bo'lsa qisqartirib ko'rsatish
    def short_text(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    short_text.short_description = "Izoh matni"