from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction, IntegrityError
from django.db.models import Count, Q
from django.contrib import messages
from utils.helpers import calculate_file_hash
from .models import Article, Category
from .forms import ArticleForm, ArticleAuthorFormSet
from communication.forms import CommentForm
from communication.models import Message, Comment
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from django.views.generic import UpdateView
from communication.models import Message
from django.views.generic import DeleteView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model



User = get_user_model()

class IndexView(View):
    def get(self, request):
        articles = Article.objects.filter(status='published').select_related('category', 'submitter')
        
        slider_articles = articles.order_by('-created_at')[:3]
        
        new_batch = list(articles.order_by('-created_at')[3:7])
        
        top_grid_articles = new_batch
        
        if len(top_grid_articles) < 4:
            needed = 4 - len(top_grid_articles)
            
            existing_ids = [a.id for a in slider_articles] + [a.id for a in top_grid_articles]
            
            popular_fill = list(articles.exclude(id__in=existing_ids).order_by('-views')[:needed])
            top_grid_articles.extend(popular_fill)

        breaking_articles = articles.order_by('-updated_at')[:5]
        featured_articles = articles.order_by('-views')[:10]
        latest_articles = articles.order_by('-created_at')[:4]
        popular_articles = articles.order_by('-views')[:5]
        special_articles = articles.filter(cover_image__isnull=False).order_by('-created_at')[:1]
        categories = Category.objects.all()

        context = {
            'slider_articles': slider_articles,
            'top_grid_articles': top_grid_articles,
            'breaking_articles': breaking_articles,
            'featured_articles': featured_articles,
            'latest_articles': latest_articles,
            'popular_articles': popular_articles,
            'special_articles': special_articles,
            'categories': categories,
        }
        return render(request, 'index.html', context)


class ArticleCreateView(LoginRequiredMixin, View):
    template_name = 'articles/article_create.html'

    def get(self, request):
        form = ArticleForm()
        formset = ArticleAuthorFormSet()
        return render(request, self.template_name, {
            'form': form, 
            'formset': formset
        })

    def post(self, request):
        form = ArticleForm(request.POST, request.FILES)
        formset = ArticleAuthorFormSet(request.POST)
        
        file_hash = None 

        if 'original_file' in request.FILES:
            uploaded_file = request.FILES['original_file']
            try:
                file_hash = calculate_file_hash(uploaded_file)
                
                # print(f"YUKLANAYOTGAN FAYL: {uploaded_file.name}")
                # print(f"HISOBLANGAN XESH:  {file_hash}")


                existing_article = Article.objects.filter(file_hash=file_hash).first()
                
                if existing_article:
                    print(f"❌ DUBLIKAT TOPILDI! ID: {existing_article.id}")
                    
                    return render(request, 'articles/duplicate_error.html', {
                        'article': existing_article,
                        'uploader': existing_article.submitter
                    })
                else:
                    print("✅ Fayl yangi, dublikat yo'q. Saqlashga o'tamiz...")

            except Exception as e:
                print(f"❌ Xesh tekshirishda xato: {e}")

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    article = form.save(commit=False)
                    article.submitter = request.user
                    article.status = 'submitted'

                    if file_hash:
                        article.file_hash = file_hash
                        print(f"💾 Xesh modelga yozildi: {article.file_hash}")
                    else:
                        print("⚠️ DIQQAT: Xesh hisoblanmadi!")

                    article.save()
                    print(f"✅ Maqola saqlandi ID: {article.id}")

                    authors = formset.save(commit=False)
                    for author in authors:
                        author.article = article
                        author.save()
                    
                    for deleted in formset.deleted_objects:
                        deleted.delete()
                    
                    Message.objects.create(
                        sender=None,
                        recipient=request.user,
                        subject="Maqola qabul qilindi",
                        body=f"Sizning '{article.title}' maqolangiz qabul qilindi. Tez orada ko'rib chiqamiz.",
                        article=article
                    )

                messages.success(request, "Maqola muvaffaqiyatli yuborildi!")
                return redirect('inbox')

            except IntegrityError:
                 print("⚠️ IntegrityError: Saqlash paytida dublikat aniqlandi.")
                 if file_hash:
                     existing = Article.objects.filter(file_hash=file_hash).first()
                     return render(request, 'articles/duplicate_error.html', {
                            'article': existing,
                            'uploader': existing.submitter if existing else None
                     })
                 else:
                     messages.error(request, "Ma'lumotlar bazasi xatoligi (IntegrityError).")

            except Exception as e:
                messages.error(request, f"Tizim xatoligi: {e}")
                print(f"❌ Saqlashda jiddiy xatolik: {e}")
        
        else:
            print("❌ Formada validatsiya xatosi bor.")
            print(form.errors)
        
        return render(request, self.template_name, {
            'form': form, 
            'formset': formset
        })


@method_decorator(xframe_options_sameorigin, name='dispatch')
class ArticleDetailView(View):
    template_name = 'articles/article_detail.html'

    def get_context_data(self, article):
        comments = article.comments.all().order_by('-created_at')
        related_articles = Article.objects.filter(
            category=article.category, 
            status='published'
        ).exclude(id=article.id)[:5]
        
        keywords_list = []
        if article.keywords:
            keywords_list = [k.strip() for k in article.keywords.split(',') if k.strip()]
        
        return {
            'article': article,
            'comments': comments,
            'related_articles': related_articles,
            'keywords_list': keywords_list,
        }

    def get(self, request, slug):
        if request.user.is_staff:
             article = get_object_or_404(Article, slug=slug)
        
        elif request.user.is_authenticated:
            article = get_object_or_404(Article, Q(status='published') | Q(submitter=request.user), slug=slug)
        
        else:
            article = get_object_or_404(Article, status='published', slug=slug)
        
        session_key = f'viewed_article_{article.id}'
        if not request.session.get(session_key, False):
            article.views += 1
            article.save(update_fields=['views'])
            request.session[session_key] = True

        context = self.get_context_data(article)
        context['comment_form'] = CommentForm()

        return render(request, self.template_name, context)

    def post(self, request, slug):
        if request.user.is_staff:
             article = get_object_or_404(Article, slug=slug)
        elif request.user.is_authenticated:
            article = get_object_or_404(Article, Q(status='published') | Q(submitter=request.user), slug=slug)
        else:
            article = get_object_or_404(Article, status='published', slug=slug)
        
        if not request.user.is_authenticated:
            messages.warning(request, "Izoh qoldirish uchun tizimga kiring.")
            return redirect('login')

        form = CommentForm(request.POST)
        
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.user = request.user
            comment.save()
            
            if article.submitter != request.user:
                
                Message.objects.create(
                    sender=request.user,
                    recipient=article.submitter,
                    article=article,
                    subject=f"Yangi izoh: {article.title}",
                    body=f"{request.user.get_full_name() or request.user.username} maqolangizga fikr bildirdi: \n\n'{comment.text}'"
                )

            return redirect('article_detail', slug=slug)
        else:
            messages.error(request, "Izoh yuborishda xatolik. Matnni tekshiring.")
            context = self.get_context_data(article)
            context['comment_form'] = form
            return render(request, self.template_name, context)

class UserDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        my_articles = Article.objects.filter(submitter=request.user).order_by('-created_at')
        return render(request, 'users/dashboard.html', {'articles': my_articles})



@method_decorator(staff_member_required, name='dispatch')
class ProcessArticleView(View):
    def post(self, request, slug):
        article = get_object_or_404(Article, slug=slug)
        action = request.POST.get('action')
        reject_reason = request.POST.get('reject_reason', '')

        recipients = set()
        
        if article.submitter:
            recipients.add(article.submitter)
            
        for author in article.authors.all():
            if author.user:
                recipients.add(author.user)

        if action == 'approve':
            article.status = 'published'
            article.is_resubmission = False
            article.save()
            
            for user in recipients:
                Message.objects.create(
                    sender=None, 
                    recipient=user,
                    article=article,
                    subject="TABRIKLAYMIZ! Maqola chop etildi",
                    body=f"Hurmatli {user.get_full_name() or user.username},\n\n"
                         f"Siz mualliflik qilgan '{article.title}' nomli maqola muvaffaqiyatli tasdiqlandi va saytga joylashtirildi."
                )

        elif action == 'reject':
            article.status = 'changes_requested' 
            article.save()
            
            for user in recipients:
                Message.objects.create(
                    sender=None,
                    recipient=user,
                    article=article,
                    subject="Maqola RAD ETILDI",
                    body=f"Hurmatli {user.get_full_name() or user.username},\n\n"
                         f"Sizning '{article.title}' nomli maqolangiz qabul qilinmadi.\n\n"
                         f"SABAB:\n{reject_reason}\n\n"
                         f"Maqolani yuklagan shaxs kamchiliklarni tuzatib, qayta yuborishi mumkin. \n\nDiqqat bu xabar tizimda profili mavjud bo'lgan shu maqola muallifi bo'lgan barchaga yetkazildi faqat yuborgan muallif yangilay oladi."
                )
            
        return redirect('moderation_list')

class AdminArticleListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Article
    template_name = 'articles/moderation_list.html'
    context_object_name = 'articles'
    paginate_by = 10 

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        queryset = Article.objects.all().order_by('-updated_at')

        status_filter = self.request.GET.get('status')
        
        if status_filter == 'resubmitted':
            queryset = queryset.filter(status='submitted', is_resubmission=True)
            
        elif status_filter == 'submitted':
            queryset = queryset.filter(status='submitted', is_resubmission=False)
            
        elif status_filter == 'rejected':
            queryset = queryset.filter(status__in=['rejected', 'changes_requested'])
            
        elif status_filter:
            queryset = queryset.filter(status=status_filter)
            
        else:
            if not self.request.GET.get('q'):
                queryset = queryset.filter(status='submitted')

        category_filter = self.request.GET.get('category')
        if category_filter:
            queryset = queryset.filter(category_id=category_filter)

        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(submitter__username__icontains=query) |
                Q(submitter__first_name__icontains=query)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['categories'] = Category.objects.all()
        context['selected_status'] = self.request.GET.get('status', '') # Defaultda
        context['selected_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('q', '')

        context['count_new'] = Article.objects.filter(status='submitted', is_resubmission=False).count()
        context['count_resubmitted'] = Article.objects.filter(status='submitted', is_resubmission=True).count()
        context['count_total_pending'] = context['count_new'] + context['count_resubmitted']
        
        return context

class ArticleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = 'articles/article_update.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def test_func(self):
        article = self.get_object()
        return self.request.user == article.submitter or self.request.user.is_staff

    def form_valid(self, form):
        try:
            with transaction.atomic():
                
                self.object = form.save(commit=False)
                self.object.status = 'submitted'
                
                self.object.is_resubmission = True
                
                self.object.save()
                Message.objects.create(
                    sender=self.request.user,
                    recipient=self.request.user,
                    article=self.object,
                    subject="Maqola tahrirlab qayta yuborildi",
                    body="Muallif kamchiliklarni tuzatib, maqolani qayta moderatsiyaga yubordi.",
                    is_read=True 
                )

                messages.success(self.request, "Maqola muvaffaqiyatli yangilandi va Adminga yuborildi. Javobni Inbox orqali kuting.")
                
                return redirect('inbox')
        
        except Exception as e:
            messages.error(self.request, f"Saqlashda xatolik yuz berdi: {e}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Formada xatoliklar mavjud. Iltimos, tekshirib qayta yuboring.")
        return super().form_invalid(form)


@method_decorator(staff_member_required, name='dispatch')
class ArticleHistoryView(View):
    template_name = 'articles/article_history.html'

    def get(self, request, slug):
        article = get_object_or_404(Article, slug=slug)
        
        history_messages = Message.objects.filter(article=article).order_by('-created_at')
        
        return render(request, self.template_name, {
            'article': article,
            'history': history_messages
        })



class ArticleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Article
    template_name = 'articles/article_confirm_delete.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    success_url = reverse_lazy('article_create') 

    def test_func(self):
        article = self.get_object()
        
        can_delete_status = ['rejected', 'changes_requested', 'submitted', 'draft']
        return article.submitter == self.request.user and article.status in can_delete_status

    def delete(self, request, *args, **kwargs):
        messages.info(self.request, "Eski maqola o'chirildi. Marhamat, tuzatilgan variantini yangidan yuklang.")
        return super().delete(request, *args, **kwargs)


class ArticleListView(ListView):
    model = Article
    template_name = 'articles/article_list.html'
    context_object_name = 'articles'
    paginate_by = 10 

    def get_queryset(self):
        queryset = Article.objects.filter(status='published').select_related('category', 'submitter').order_by('-created_at')

        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        year = self.request.GET.get('year')
        if year:
            queryset = queryset.filter(year=year)

        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(abstract__icontains=query)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        cat_id = self.request.GET.get('category')
        if cat_id:
            context['current_category'] = Category.objects.filter(id=cat_id).first()
        
        context['categories'] = Category.objects.annotate(count=Count('articles')).order_by('name')
        
        context['popular_articles'] = Article.objects.filter(status='published').order_by('-views')[:5]
        
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['selected_year'] = self.request.GET.get('year', '')
        
        return context


class ContactView(View):
    def get(self, request):
        return render(request, 'contact.html')



class AuthorListView(ListView):
    model = User
    template_name = 'articles/author_list.html'
    context_object_name = 'authors'
    paginate_by = 12

    def get_queryset(self):
        
        queryset = User.objects.filter(is_active=True).annotate(
            num_posts=Count('submitted_articles', filter=Q(submitted_articles__status='published'))
        ).order_by('-num_posts')

        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['categories'] = Category.objects.annotate(count=Count('articles')).order_by('-count')
        
        context['popular_articles'] = Article.objects.filter(status='published').order_by('-views')[:5]
        
        context['search_query'] = self.request.GET.get('q', '')
        
        return context