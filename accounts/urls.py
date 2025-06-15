from email.parser import Parser
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import JsonResponse

from accounts.models import User
from order.models import Order
from products.models import Product
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
     path('', views.dashboard_redirect, name='dashboard'),

     path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
     path('buyer-dashboard/', views.buyer_dashboard, name='buyer_dashboard'),
     path('farmer-dashboard/', views.farmer_dashboard, name='farmer_dashboard'),

     # Additional views
     path('profile-setup/', views.profile_setup, name='profile_setup'),
     path('switch-role/', views.switch_role, name='switch_role'),
     path('dashboard-stats-api/', views.dashboard_stats_api, name='dashboard_stats_api'),
]

@login_required
def dashboard_redirect(request):
    """Redirect users to appropriate dashboard based on their role"""
    user = request.user
    
    if user.is_superuser or user.is_staff:
        return redirect('admin_dashboard')
    elif hasattr(user, 'farmer_profile'):
        return redirect('farmer_dashboard')
    elif hasattr(user, 'buyer_profile'):
        return redirect('buyer_dashboard')
    else:
        # Default redirect or create profile
        messages.info(request, 'Please complete your profile setup.')
        return redirect('profile_setup')

@login_required
def buyer_dashboard(request):
    """Buyer dashboard view"""
    if not hasattr(request.user, 'buyer_profile'):
        messages.error(request, 'Access denied. Buyer profile required.')
        return redirect('dashboard')
    
    buyer = request.user.buyer_profile
    
    # Get statistics
    total_orders = Order.objects.filter(buyer=buyer).count()
    pending_orders = Order.objects.filter(buyer=buyer, status='pending').count()
    favorite_products = buyer.favorite_products.count() if hasattr(buyer, 'favorite_products') else 0
    total_spent = Order.objects.filter(
        buyer=buyer, 
        status='completed'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Get recent orders (last 5)
    recent_orders = Order.objects.filter(buyer=buyer).select_related(
        'supplier__user', 'product'
    ).order_by('-created_at')[:5]
    
    # Get new products (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    new_products = Product.objects.filter(
        created_at__gte=week_ago,
        is_active=True
    ).select_related('farmer__user').order_by('-created_at')[:5]
    
    # Get recent activities (customize based on your activity model)
    recent_activities = []
    
    # Get unread messages count
    unread_messages_count = 0
    if hasattr(buyer, 'received_messages'):
        unread_messages_count = buyer.received_messages.filter(is_read=False).count()
    
    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'favorite_products': favorite_products,
        'total_spent': total_spent,
        'recent_orders': recent_orders,
        'new_products': new_products,
        'recent_activities': recent_activities,
        'unread_messages_count': unread_messages_count,
    }
    
    return render(request, 'buyer_dashboard.html', context)

@staff_member_required
def admin_dashboard(request):
    """Admin dashboard view"""
    
    # Get overall statistics
    total_users = User.objects.count()
    total_farmers = User.objects.filter(farmer_profile__isnull=False).count()
    total_buyers = User.objects.filter(buyer_profile__isnull=False).count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    
    # Get recent registrations (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_users = User.objects.filter(date_joined__gte=thirty_days_ago).count()
    new_farmers = User.objects.filter(
        farmer_profile__isnull=False,
        date_joined__gte=thirty_days_ago
    ).count()
    new_buyers = User.objects.filter(
        buyer_profile__isnull=False,
        date_joined__gte=thirty_days_ago
    ).count()
    
    # Revenue statistics
    total_revenue = Order.objects.filter(
        status='completed'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    monthly_revenue = Order.objects.filter(
        status='completed',
        created_at__month=timezone.now().month,
        created_at__year=timezone.now().year
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Recent orders
    recent_orders = Order.objects.select_related(
        'buyer__user', 'supplier__user', 'product'
    ).order_by('-created_at')[:10]
    
    # Top products
    top_products = Product.objects.annotate(
        order_count=Count('order')
    ).order_by('-order_count')[:5]
    
    # Top farmers by sales
    top_farmers = User.objects.filter(
        farmer_profile__isnull=False
    ).annotate(
        total_sales=Sum('farmer_profile__products__order__total_amount')
    ).order_by('-total_sales')[:5]
    
    # Pending approvals (if you have approval system)
    pending_farmers = User.objects.filter(
        farmer_profile__is_approved=False
    ).count() if hasattr(Parser, 'is_approved') else 0
    
    pending_products = Product.objects.filter(
        is_approved=False
    ).count() if hasattr(Product, 'is_approved') else 0
    
    context = {
        'total_users': total_users,
        'total_farmers': total_farmers,
        'total_buyers': total_buyers,
        'total_products': total_products,
        'total_orders': total_orders,
        'new_users': new_users,
        'new_farmers': new_farmers,
        'new_buyers': new_buyers,
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'recent_orders': recent_orders,
        'top_products': top_products,
        'top_farmers': top_farmers,
        'pending_farmers': pending_farmers,
        'pending_products': pending_products,
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
def dashboard_stats_api(request):
    """API endpoint for dashboard statistics (for AJAX updates)"""
    user = request.user
    stats = {}
    
    if hasattr(user, 'farmer_profile'):
        farmer = user.farmer_profile
        stats = {
            'total_products': farmer.products.count(),
            'active_products': farmer.products.filter(is_active=True).count(),
            'total_orders': Order.objects.filter(supplier=farmer).count(),
            'pending_orders': Order.objects.filter(supplier=farmer, status='pending').count(),
        }
    elif hasattr(user, 'buyer_profile'):
        buyer = user.buyer_profile
        stats = {
            'total_orders': Order.objects.filter(buyer=buyer).count(),
            'pending_orders': Order.objects.filter(buyer=buyer, status='pending').count(),
            'favorite_products': buyer.favorite_products.count() if hasattr(buyer, 'favorite_products') else 0,
        }
    
    return JsonResponse(stats)

# Additional helper views

@login_required
def profile_setup(request):
    """Profile setup view for new users"""
    if request.method == 'POST':
        role = request.POST.get('role')
        if role == 'farmer':
            # Create farmer profile
            farmer, created = farmer.objects.get_or_create(user=request.user)
            return redirect('farmer_dashboard')
        elif role == 'buyer':
            # Create buyer profile
            buyer, created = buyer.objects.get_or_create(user=request.user)
            return redirect('buyer_dashboard')
    
    return render(request, 'profile_setup.html')

@login_required  
def switch_role(request):
    """Allow users to switch between farmer and buyer roles if they have both"""
    user = request.user
    current_role = request.session.get('current_role', 'farmer')
    
    if request.method == 'POST':
        new_role = request.POST.get('role')
        if new_role in ['farmer', 'buyer']:
            # Check if user has the requested role
            if new_role == 'farmer' and hasattr(user, 'farmer_profile'):
                request.session['current_role'] = 'farmer'
                return redirect('farmer_dashboard')
            elif new_role == 'buyer' and hasattr(user, 'buyer_profile'):
                request.session['current_role'] = 'buyer'
                return redirect('buyer_dashboard')
    
    context = {
        'current_role': current_role,
        'has_farmer_profile': hasattr(user, 'farmer_profile'),
        'has_buyer_profile': hasattr(user, 'buyer_profile'),
    }
    return render(request, 'switch_role.html', context)