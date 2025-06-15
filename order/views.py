from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.http import HttpResponseForbidden
from .models import Order, OrderItem
from cart.cart import Cart
from products.models import Product
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_POST
from .forms import OrderCreateForm, OrderStatusForm, OrderItemForm
from .forms import OrderCreateForm

def order_list(request):
    """Display list of orders with search and filter functionality"""
    orders = Order.objects.all().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        orders = orders.filter(
            Q(id__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Status filter
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        orders = orders.filter(status=status_filter)
    
    context = {
        'orders': orders,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'order/order_list.html', context)

def order_detail(request, order_id):
    """Display detailed view of a specific order"""
    order = get_object_or_404(Order, id=order_id)
    context = {
        'order': order,
    }
    return render(request, 'orders/order_detail.html', context)

def order_create(request):
    """Create a new order"""
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save()
            messages.success(request, f'Order {order.order_id} created successfully!')
            return redirect('orders:order_detail', order_id=order.id)
    else:
        form = OrderCreateForm()
    
    context = {
        'form': form,
    }
    return render(request, 'orders/order_create.html', context)

@require_POST
def update_order_status(request, order_id):
    """Update order status via AJAX"""
    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status')
    
    if new_status in dict(Order.STATUS_CHOICES):
        order.status = new_status
        order.save()
        return JsonResponse({'success': True, 'message': 'Status updated successfully'})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid status'})

@require_POST
def delete_order(request, order_id):
    """Delete an order"""
    order = get_object_or_404(Order, id=order_id)
    order_number = order.order_id
    order.delete()
    messages.success(request, f'Order {order_number} has been deleted successfully.')
    return redirect('orders:order_list')

