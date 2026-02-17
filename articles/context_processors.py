from .models import Article, Category

def footer_context(request):
    """
    Saytning barcha sahifalarida Footer uchun kerakli ma'lumotlarni chiqaradi.
    """
    # 1. Eng ko'p o'qilgan 3 ta maqola (Footer uchun)
    footer_popular = Article.objects.filter(status='published').order_by('-views')[:5]
    
    # 2. Barcha kategoriyalar
    footer_categories = Category.objects.all()[:20]

    return {
        'footer_popular': footer_popular,
        'footer_categories': footer_categories,
    }