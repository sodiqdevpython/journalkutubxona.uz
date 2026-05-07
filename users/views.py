from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from .forms import UserRegistrationForm, UserLoginForm
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import CustomUser
from django.views.generic import DetailView
from django.contrib.auth import get_user_model
from articles.models import Article
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from .forms import UserUpdateForm


User = get_user_model()

class RegisterView(SuccessMessageMixin, CreateView):
    template_name = 'users/register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('login') 
    success_message = "Siz muvaffaqiyatli ro'yxatdan o'tdingiz! Endi kirishingiz mumkin."

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)

class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    authentication_form = UserLoginForm
    redirect_authenticated_user = True 
    
    def get_success_url(self):
        return reverse_lazy('index') 

class CustomLogoutView(LogoutView):
    next_page = 'index'


@login_required
def search_users(request):
    query = request.GET.get('q', '')
    if query:
        
        users = CustomUser.objects.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query)
        ).values('id', 'username', 'first_name', 'last_name')[:20] 
        
        results = []
        for user in users:
            full_name = f"{user['first_name']} {user['last_name']}".strip()
            text = f"{full_name} ({user['username']})" if full_name else user['username']
            results.append({'id': user['id'], 'text': text})
            
        return JsonResponse({'results': results})
    return JsonResponse({'results': []})



class UserProfileView(DetailView):
    model = User
    template_name = 'users/profile_detail.html'
    context_object_name = 'profile_user'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object 

        
        
        articles_list = Article.objects.filter(
            submitter=user, 
            status='published'
        ).order_by('-created_at')

        
        paginator = Paginator(articles_list, 5)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['articles'] = page_obj 
        context['page_obj'] = page_obj 
        context['total_articles_count'] = articles_list.count() 

        return context


class UserProfileEditView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'users/profile_edit.html'
    
    def get_success_url(self):
        return reverse_lazy('user_profile', kwargs={'username': self.request.user.username})

    def get_object(self):
        return self.request.user