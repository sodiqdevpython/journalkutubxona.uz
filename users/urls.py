from django.urls import path
from .views import RegisterView, CustomLoginView, CustomLogoutView, search_users, UserProfileView, UserProfileEditView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('search/', search_users, name='search_users'),
    path('profile/<str:username>/', UserProfileView.as_view(), name='user_profile'),
    path('profile/edit/me/', UserProfileEditView.as_view(), name='profile_edit'),
]