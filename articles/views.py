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

# ---------------------------------------------------------
# 1. BOSH SAHIFA (INDEX) - O'qish (Read)
# ---------------------------------------------------------
class IndexView(View):
    def get(self, request):
        # 1. Faqat chop etilgan maqolalar
        articles = Article.objects.filter(status='published').select_related('category', 'submitter')
        
        # 2. Katta Slider (Eng yangi 3 ta)
        slider_articles = articles.order_by('-created_at')[:3]
        
        # 3. O'ng tomon Grid (Keyingi 4 ta)
        # Oldin eng yangilarini olamiz (sliderdagilardan keyingi)
        new_batch = list(articles.order_by('-created_at')[3:7])
        
        top_grid_articles = new_batch
        
        # AGAR 4 TAdan KAM BO'LSA -> Ommabop maqolalar bilan to'ldiramiz
        if len(top_grid_articles) < 4:
            needed = 4 - len(top_grid_articles)
            
            # Sliderda va Hozirgina olinganlarda borlarini chiqarib tashlaymiz
            existing_ids = [a.id for a in slider_articles] + [a.id for a in top_grid_articles]
            
            # Eng ko'p ko'rilganlardan olamiz
            popular_fill = list(articles.exclude(id__in=existing_ids).order_by('-views')[:needed])
            top_grid_articles.extend(popular_fill)

        # 4. Qolgan qismlar (O'zgarishsiz)
        breaking_articles = articles.order_by('-updated_at')[:5]
        featured_articles = articles.order_by('-views')[:10]
        latest_articles = articles.order_by('-created_at')[:20]
        popular_articles = articles.order_by('-views')[:5]
        special_articles = articles.filter(cover_image__isnull=False).order_by('-created_at')[:1]
        categories = Category.objects.all()

        context = {
            'slider_articles': slider_articles,
            'top_grid_articles': top_grid_articles, # Endi bu har doim to'la bo'ladi
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
        
        # O'zgaruvchini oldindan e'lon qilamiz
        file_hash = None 

        # -----------------------------------------------------------
        # 1-QADAM: FAYL DUBLIKATINI TEKSHIRISH
        # -----------------------------------------------------------
        if 'original_file' in request.FILES:
            uploaded_file = request.FILES['original_file']
            try:
                # 1. Xeshni hisoblaymiz (Helper funksiya seek(0) qilishi shart!)
                file_hash = calculate_file_hash(uploaded_file)
                
                # --- DEBUG PRINT (Terminalda tekshiring) ---
                print("\n" + "="*40)
                print(f"📂 YUKLANAYOTGAN FAYL: {uploaded_file.name}")
                print(f"🔑 HISOBLANGAN XESH:  {file_hash}")
                print("="*40 + "\n")
                # -------------------------------------------

                # 2. Bazadan shu xesh bilan fayl bormi yo'qmi qidiramiz
                existing_article = Article.objects.filter(file_hash=file_hash).first()
                
                if existing_article:
                    print(f"❌ DUBLIKAT TOPILDI! ID: {existing_article.id}")
                    
                    # AGAR TOPILSA -> Dublikat xatolik sahifasiga yuboramiz
                    return render(request, 'articles/duplicate_error.html', {
                        'article': existing_article,
                        'uploader': existing_article.submitter
                    })
                else:
                    print("✅ Fayl yangi, dublikat yo'q. Saqlashga o'tamiz...")

            except Exception as e:
                print(f"❌ Xesh tekshirishda xato: {e}")

        # -----------------------------------------------------------
        # 2-QADAM: SAQLASH JARAYONI
        # -----------------------------------------------------------
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    article = form.save(commit=False)
                    article.submitter = request.user
                    article.status = 'submitted'
                    
                    # --- ENG MUHIM TUZATISH ---
                    # Hisoblangan xeshni modelga majburan yozamiz!
                    if file_hash:
                        article.file_hash = file_hash
                        print(f"💾 Xesh modelga yozildi: {article.file_hash}")
                    else:
                        print("⚠️ DIQQAT: Xesh hisoblanmadi!")
                    # --------------------------

                    article.save()
                    print(f"✅ Maqola saqlandi ID: {article.id}")

                    # Mualliflarni saqlash
                    authors = formset.save(commit=False)
                    for author in authors:
                        author.article = article
                        author.save()
                    
                    # O'chirilganlarni tozalash
                    for deleted in formset.deleted_objects:
                        deleted.delete()
                    
                    # Inbox xabari
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
                 # Agar poyga holati (race condition) bo'lib, save() paytida dublikat aniqlansa
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
        
        # --- YANGI QO'SHILGAN QISM: KEYWORDS ---
        keywords_list = []
        if article.keywords:
            # Vergul bo'yicha ajratamiz va ortiqcha bo'sh joylarni tozalaymiz
            keywords_list = [k.strip() for k in article.keywords.split(',') if k.strip()]
        # ---------------------------------------
        
        return {
            'article': article,
            'comments': comments,
            'related_articles': related_articles,
            'keywords_list': keywords_list, # Shablonga yuboramiz
        }

    def get(self, request, slug):
        # --- MANTIQ O'ZGARDI ---
        # 1. Agar foydalanuvchi Admin bo'lsa -> Hamma narsani ko'ra oladi
        if request.user.is_staff:
             article = get_object_or_404(Article, slug=slug)
        
        # 2. Agar foydalanuvchi tizimga kirgan bo'lsa -> (Published) YOKI (O'zining maqolasi)
        elif request.user.is_authenticated:
            article = get_object_or_404(Article, Q(status='published') | Q(submitter=request.user), slug=slug)
        
        # 3. Mehmonlar -> Faqat (Published)
        else:
            article = get_object_or_404(Article, status='published', slug=slug)
        
        # --- VIEW COUNTER ---
        session_key = f'viewed_article_{article.id}'
        if not request.session.get(session_key, False):
            article.views += 1
            article.save(update_fields=['views'])
            request.session[session_key] = True

        context = self.get_context_data(article)
        context['comment_form'] = CommentForm()

        return render(request, self.template_name, context)

    def post(self, request, slug):
        # --- POST UCHUN HAM SHU MANTIQ ---
        if request.user.is_staff:
             article = get_object_or_404(Article, slug=slug)
        elif request.user.is_authenticated:
            article = get_object_or_404(Article, Q(status='published') | Q(submitter=request.user), slug=slug)
        else:
            # Aslida login_required decorator bor, lekin xavfsizlik uchun
            article = get_object_or_404(Article, status='published', slug=slug)
        
        # Faqat ro'yxatdan o'tganlar izoh yozishi mumkin
        if not request.user.is_authenticated:
            messages.warning(request, "Izoh qoldirish uchun tizimga kiring.")
            return redirect('login')

        form = CommentForm(request.POST)
        
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.user = request.user
            comment.save()
            
            # MUALLIFGA XABAR YUBORISH
            if article.submitter != request.user:
                # Importni unutmang: from communication.models import Message
                
                Message.objects.create(
                    sender=request.user,
                    recipient=article.submitter,
                    article=article,
                    subject=f"Yangi izoh: {article.title}",
                    body=f"{request.user.get_full_name() or request.user.username} maqolangizga fikr bildirdi: \n\n'{comment.text}'"
                )

            # messages.success(request, "Izohingiz qo'shildi!")
            return redirect('article_detail', slug=slug)
        else:
            messages.error(request, "Izoh yuborishda xatolik. Matnni tekshiring.")
            context = self.get_context_data(article)
            context['comment_form'] = form
            return render(request, self.template_name, context)

# Vaqtinchalik Dashboard (Keyinroq to'ldiramiz)
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

        # 1. Xabar oluvchilarni yig'amiz (Set ishlatamiz, dublikat bo'lmasligi uchun)
        recipients = set()
        
        # A) Maqolani yuklagan odam (Submitter)
        if article.submitter:
            recipients.add(article.submitter)
            
        # B) Tizimdagi boshqa mualliflar (ArticleAuthor modelidan)
        for author in article.authors.all():
            if author.user: # Agar user biriktirilgan bo'lsa (qo'lda yozilmagan bo'lsa)
                recipients.add(author.user)

        if action == 'approve':
            article.status = 'published'
            article.is_resubmission = False # Sikl tugadi, endi u yangi emas
            article.save()
            
            # HAMMAGA XABAR YUBORISH
            for user in recipients:
                Message.objects.create(
                    sender=None, # Tizimdan
                    recipient=user,
                    article=article,
                    subject="TABRIKLAYMIZ! Maqola chop etildi",
                    body=f"Hurmatli {user.get_full_name() or user.username},\n\n"
                         f"Siz mualliflik qilgan '{article.title}' nomli maqola muvaffaqiyatli tasdiqlandi va saytga joylashtirildi."
                )
            # messages.success(request, f"Maqola tasdiqlandi. {len(recipients)} ta muallifga xabar yuborildi.")

        elif action == 'reject':
            article.status = 'changes_requested'  # <--- O'ZGARISH: 'rejected' o'rniga
            article.save()
            
            # HAMMAGA XABAR YUBORISH
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
            # messages.warning(request, f"Maqola rad etildi. {len(recipients)} ta muallifga xabar yuborildi.")

        return redirect('moderation_list')

class AdminArticleListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Article
    template_name = 'articles/moderation_list.html'
    context_object_name = 'articles'
    paginate_by = 10 

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        # Default: Eng so'nggi o'zgarganlar tepada
        queryset = Article.objects.all().order_by('-updated_at')

        status_filter = self.request.GET.get('status')
        
        # 1. STATUS FILTER LOGIKASI
        if status_filter == 'resubmitted':
            # Faqat qayta yuborilganlar (Submitted + Flag True)
            queryset = queryset.filter(status='submitted', is_resubmission=True)
            
        elif status_filter == 'submitted':
            # Faqat YANGI kelganlar (Submitted + Flag False)
            queryset = queryset.filter(status='submitted', is_resubmission=False)
            
        elif status_filter == 'rejected':
            # Rad etilganlar VA Tahrirga qaytarilganlar
            queryset = queryset.filter(status__in=['rejected', 'changes_requested'])
            
        elif status_filter:
            # Boshqa aniq status (masalan: published)
            queryset = queryset.filter(status=status_filter)
            
        else:
            # Agar hech narsa tanlanmasa va qidiruv bo'lmasa -> Barcha Kutilayotganlar (Yangi + Qayta)
            if not self.request.GET.get('q'):
                queryset = queryset.filter(status='submitted')

        # 2. CATEGORY FILTER
        category_filter = self.request.GET.get('category')
        if category_filter:
            queryset = queryset.filter(category_id=category_filter)

        # 3. SEARCH
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
        
        # Filtrlarni saqlab qolish
        context['categories'] = Category.objects.all()
        context['selected_status'] = self.request.GET.get('status', '') # Default bo'sh
        context['selected_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('q', '')
        
        # --- STATISTIKA (Sidebar uchun) ---
        # 1. Yangi kutilayotganlar
        context['count_new'] = Article.objects.filter(status='submitted', is_resubmission=False).count()
        # 2. Qayta yuborilganlar
        context['count_resubmitted'] = Article.objects.filter(status='submitted', is_resubmission=True).count()
        # 3. Jami kutilayotgan (Tepada katta qilib ko'rsatish uchun)
        context['count_total_pending'] = context['count_new'] + context['count_resubmitted']
        
        return context

class ArticleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = 'articles/article_update.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    # 1. XAVFSIZLIK: Faqat maqola egasi (submitter) yoki Admin o'zgartira oladi
    def test_func(self):
        article = self.get_object()
        return self.request.user == article.submitter or self.request.user.is_staff

    # 2. SAQLASH JARAYONI
    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Formadagi ma'lumotlarni olamiz (lekin hali bazaga yozmaymiz)
                self.object = form.save(commit=False)
                
                # --- MANTIQIY O'ZGARISHLAR ---
                # Statusni majburan 'submitted' (Kutilmoqda) qilamiz
                self.object.status = 'submitted'
                
                # "Qayta yuborilgan" bayrog'ini yoqamiz (Admin bilishi uchun)
                self.object.is_resubmission = True
                
                # Endi o'zgarishlarni saqlaymiz
                self.object.save()

                # 3. TARIX UCHUN XABAR YARATISH
                # Bu xabar admin "Tarix" (History) bo'limiga kirganda ko'rinadi
                Message.objects.create(
                    sender=self.request.user,
                    recipient=self.request.user, # Yoki tizim adminiga
                    article=self.object,
                    subject="Maqola tahrirlab qayta yuborildi",
                    body="Muallif kamchiliklarni tuzatib, maqolani qayta moderatsiyaga yubordi.",
                    is_read=True # Bu shunchaki log bo'lgani uchun o'qilgan deb belgilaymiz
                )

                messages.success(self.request, "Maqola muvaffaqiyatli yangilandi va Adminga yuborildi. Javobni Inbox orqali kuting.")
                
                # 4. INBOXGA YO'NALTIRISH
                return redirect('inbox')
        
        except Exception as e:
            messages.error(self.request, f"Saqlashda xatolik yuz berdi: {e}")
            return self.form_invalid(form)

    # Agar formada xatolik bo'lsa (masalan fayl formati noto'g'ri)
    def form_invalid(self, form):
        messages.error(self.request, "Formada xatoliklar mavjud. Iltimos, tekshirib qayta yuboring.")
        return super().form_invalid(form)


@method_decorator(staff_member_required, name='dispatch')
class ArticleHistoryView(View):
    template_name = 'articles/article_history.html'

    def get(self, request, slug):
        article = get_object_or_404(Article, slug=slug)
        
        # Shu maqolaga tegishli barcha xabarlar (Rad etish sabablari, tasdiqlashlar)
        # Sana bo'yicha saralangan
        history_messages = Message.objects.filter(article=article).order_by('-created_at')
        
        return render(request, self.template_name, {
            'article': article,
            'history': history_messages
        })



class ArticleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Article
    template_name = 'articles/article_confirm_delete.html' # Buni pastda yasaymiz
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    # O'chirilgandan keyin to'g'ri "Yangi Maqola Yuborish"ga o'tadi
    success_url = reverse_lazy('article_create') 

    def test_func(self):
        article = self.get_object()
        # Faqat o'zining maqolasi bo'lsa VA statusi 'rejected' yoki 'changes_requested' bo'lsa o'chira oladi
        # Tasdiqlangan maqolani o'chirib yubormasligi kerak!
        can_delete_status = ['rejected', 'changes_requested', 'submitted', 'draft']
        return article.submitter == self.request.user and article.status in can_delete_status

    def delete(self, request, *args, **kwargs):
        messages.info(self.request, "Eski maqola o'chirildi. Marhamat, tuzatilgan variantini yangidan yuklang.")
        return super().delete(request, *args, **kwargs)



class ArticleListView(ListView):
    model = Article
    template_name = 'articles/article_list.html'
    context_object_name = 'articles'
    paginate_by = 10  # Bir sahifada 10 ta maqola

    def get_queryset(self):
        # 1. Boshlang'ich: Faqat chop etilgan maqolalar
        queryset = Article.objects.filter(status='published').select_related('category', 'submitter').order_by('-created_at')

        # 2. FILTER: Kategoriya bo'yicha (?category=3)
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # 3. QIDIRUV: Sarlavha yoki Annotatsiya bo'yicha (?q=matn)
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(abstract__icontains=query)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Hozirgi tanlangan kategoriya (Title da chiqarish uchun)
        cat_id = self.request.GET.get('category')
        if cat_id:
            context['current_category'] = Category.objects.filter(id=cat_id).first()
        
        # Sidebar: Kategoriyalar ro'yxati (maqolalar soni bilan)
        context['categories'] = Category.objects.annotate(count=Count('articles')).order_by('name')
        
        # Sidebar: Ko'p o'qilganlar
        context['popular_articles'] = Article.objects.filter(status='published').order_by('-views')[:5]
        
        # Filtrlarni paginationda saqlab qolish uchun
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_category'] = self.request.GET.get('category', '')
        
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
        # 1. Userlar uchun: 'submitted_articles' (Avvalgi xatodan to'g'rilandi)
        queryset = User.objects.filter(is_active=True).annotate(
            num_posts=Count('submitted_articles', filter=Q(submitted_articles__status='published'))
        ).order_by('-num_posts')

        # 2. Qidiruv
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
        
        # --- TUZATILDI ---
        # Xatolik: "Cannot resolve keyword 'article_set'... Choices are: articles"
        # Demak, bu yerda 'articles' ishlatish kerak.
        context['categories'] = Category.objects.annotate(count=Count('articles')).order_by('-count')
        
        # Sidebar: Ko'p o'qilganlar
        context['popular_articles'] = Article.objects.filter(status='published').order_by('-views')[:5]
        
        # Search query
        context['search_query'] = self.request.GET.get('q', '')
        
        return context