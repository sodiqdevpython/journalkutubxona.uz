from django.db import models
from django.conf import settings
from utils.models import BaseModel
from articles.models import Article

class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True, blank=True) # Qaysi maqola haqida?
    
    subject = models.CharField(max_length=255) # Mavzu
    body = models.TextField() # Xabar matni
    is_read = models.BooleanField(default=False) # O'qilganmi?
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at'] # Yangilari tepada

    def __str__(self):
        return f"{self.subject} - {self.recipient}"

class Comment(BaseModel):
    # Bu yerda ham 'articles.Article' string ko'rinishida
    article = models.ForeignKey('articles.Article', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField(verbose_name="Izoh")

    class Meta:
        ordering = ['created_at']
        verbose_name = "Izoh"
        verbose_name_plural = "Izohlar"

    def __str__(self):
        return f"Comment by {self.user}"