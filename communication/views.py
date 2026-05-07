from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Message

class InboxView(LoginRequiredMixin, View):
    template_name = 'communication/inbox.html'

    def get(self, request):
        
        messages_list = Message.objects.filter(recipient=request.user).order_by('-created_at')

        status = request.GET.get('status')
        if status == 'unread':
            messages_list = messages_list.filter(is_read=False)
        elif status == 'read':
            messages_list = messages_list.filter(is_read=True)

        query = request.GET.get('q')
        if query:
            messages_list = messages_list.filter(
                Q(subject__icontains=query) | 
                Q(body__icontains=query)
            )

        paginator = Paginator(messages_list, 10) 
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'messages': page_obj,
            'filter_status': status,
            'search_query': query
        }
        return render(request, self.template_name, context)


class MessageDetailView(LoginRequiredMixin, View):
    template_name = 'communication/message_detail.html'

    def get(self, request, pk):
        message = get_object_or_404(Message, pk=pk, recipient=request.user)
        
        if not message.is_read:
            message.is_read = True
            message.save()
        
        return render(request, self.template_name, {'message': message})