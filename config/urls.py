from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render

from communication.views import InboxView, MessageDetailView
from articles.views import ProcessArticleView


def custom_404(request, exception):
    """
    404 xatoligi yuz berganda ishlaydigan maxsus view.
    """
    return render(request, '404.html', status=404)


handler404 = custom_404


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('articles.urls')),
    path('users/', include('users.urls')),
    path('inbox/', InboxView.as_view(), name='inbox'),
    path('inbox/<int:pk>/', MessageDetailView.as_view(), name='message_detail'),
    path('article/<slug:slug>/process/', ProcessArticleView.as_view(), name='process_article'),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)