from django.urls import path
from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('dashboard/', views.UserDashboardView.as_view(), name='user_dashboard'),
    path('article/add/', views.ArticleCreateView.as_view(), name='article_create'),
    path('article/<slug:slug>/', views.ArticleDetailView.as_view(), name='article_detail'),
    path('moderation/', views.AdminArticleListView.as_view(), name='moderation_list'),
    path('article/<slug:slug>/process/', views.ProcessArticleView.as_view(), name='process_article'),
    path('article/<slug:slug>/edit/', views.ArticleUpdateView.as_view(), name='article_update'),
    path('article/<slug:slug>/history/', views.ArticleHistoryView.as_view(), name='article_history'),
    path('article/<slug:slug>/delete/', views.ArticleDeleteView.as_view(), name='article_delete'),
    path('news/', views.ArticleListView.as_view(), name='article_list'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('authors/', views.AuthorListView.as_view(), name='author_list')
]
