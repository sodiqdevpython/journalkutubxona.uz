from .models import Article, Category

def footer_context(request):
    """
    Saytning barcha sahifalarida Footer uchun kerakli ma'lumotlarni chiqaradi.
    """
    footer_popular = Article.objects.filter(status='published').order_by('-views')[:5]
    
    footer_categories = Category.objects.all()[:20]

    return {
        'footer_popular': footer_popular,
        'footer_categories': footer_categories,
    }