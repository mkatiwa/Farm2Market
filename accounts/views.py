from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
from collections import Counter

from .models import User, FarmerProfile, BuyerProfile
from products.models import Product
from order.models import Order


@login_required
def dashboard_redirect(request):
    """Redirect users to their appropriate dashboard based on user type"""
    user = request.user
    
    # Check if user is admin/staff
    if user.is_superuser or user.is_staff:
        return redirect('accounts:admin_dashboard')
    
    # Check user type if it exists
    if hasattr(user, 'user_type'):
        if user.user_type == 'farmer':
            return redirect('accounts:farmer_dashboard')
        elif user.user_type == 'buyer':
            return redirect('accounts:buyer_dashboard')
        elif user.user_type == 'admin':
            return redirect('accounts:admin_dashboard')
    
    # Check for profile attributes
    if hasattr(user, 'farmer_profile') and user.farmer_profile:
        return redirect('accounts:farmer_dashboard')
    elif hasattr(user, 'buyer_profile') and user.buyer_profile:
        return redirect('accounts:buyer_dashboard')
    
    # If no specific role found, redirect to profile setup
    messages.info(request, 'Please complete your profile setup.')
    return redirect('accounts:profile_setup')


@login_required
def farmer_dashboard(request):
    """Dashboard for farmers"""
    user = request.user
    
    # Check access permissions
    has_farmer_access = (
        (hasattr(user, 'user_type') and user.user_type == 'farmer') or
        (hasattr(user, 'farmer_profile') and user.farmer_profile) or
        user.is_staff
    )
    
    if not has_farmer_access:
        messages.error(request, 'Access denied. Farmer account required.')
        return redirect('accounts:dashboard')
    
    # Get farmer's products and statistics
    products = Product.objects.filter(farmer=user)
    total_products = products.count()
    active_products = products.filter(is_active=True).count()
    
    # Get recent orders for farmer's products
    recent_orders = Order.objects.filter(
        items__product__farmer=user
    ).distinct().order_by('-created')[:10]
    
    # Calculate revenue (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    monthly_revenue = Order.objects.filter(
        items__product__farmer=user,
        created__gte=thirty_days_ago,  # Fixed: using 'created' not 'created_at'
        status='completed'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Low stock products
    low_stock_products = products.filter(stock__lt=10, is_active=True)
    
    # Total orders received
    total_orders = Order.objects.filter(items__product__farmer=user).distinct().count()
    pending_orders = Order.objects.filter(
        items__product__farmer=user, 
        status='pending'
    ).distinct().count()
    
    context = {
        'total_products': total_products,
        'active_products': active_products,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'recent_orders': recent_orders,
        'monthly_revenue': monthly_revenue,
        'low_stock_products': low_stock_products,
        'products': products[:5],  # Recent 5 products
    }
    return render(request, 'accounts/farmer_dashboard.html', context)


@login_required
def buyer_dashboard(request):
    """Dashboard for buyers"""
    user = request.user
    
    # Check access permissions
    has_buyer_access = (
        (hasattr(user, 'user_type') and user.user_type == 'buyer') or
        (hasattr(user, 'buyer_profile') and user.buyer_profile) or
        user.is_staff
    )
    
    if not has_buyer_access:
        messages.error(request, 'Access denied. Buyer account required.')
        return redirect('accounts:dashboard')
    
    # Get buyer's orders and statistics
    orders = Order.objects.filter(user=user)
    total_orders = orders.count()
    pending_orders = orders.filter(status='pending').count()
    completed_orders = orders.filter(status='completed').count()
    
    # Recent orders
    recent_orders = orders.order_by('-created_at')[:10]
    
    # Calculate total spent (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    monthly_spending = orders.filter(
        created_at__gte=thirty_days_ago,
        status='completed'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Total spent overall
    total_spent = orders.filter(status='completed').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Favorite products (most ordered)
    favorite_products = []
    try:
        if orders.exists():
            all_items = []
            for order in orders.filter(status='completed'):
                if hasattr(order, 'items'):
                    all_items.extend([item.product for item in order.items.all()])
            
            if all_items:
                product_counts = Counter(all_items)
                favorite_products = [product for product, count in product_counts.most_common(5)]
    except:
        pass  # Handle any potential errors gracefully
    
    # New products (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    new_products = Product.objects.filter(
        created_at__gte=week_ago,  # Fixed: using 'created_at' for Product model
        is_active=True
    ).order_by('-created_at')[:5]  # Fixed: using 'created_at' for Product model
    
    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'recent_orders': recent_orders,
        'monthly_spending': monthly_spending,
        'total_spent': total_spent,
        'favorite_products': favorite_products,
        'new_products': new_products,
    }
    return render(request, 'accounts/buyer_dashboard.html', context)


@staff_member_required
def admin_dashboard(request):
    """Dashboard for admin users"""
    # Overall statistics
    total_users = User.objects.count()
    
    # Count users by type
    if hasattr(User, 'user_type'):
        total_farmers = User.objects.filter(user_type='farmer').count()
        total_buyers = User.objects.filter(user_type='buyer').count()
    else:
        # Fallback to profile-based counting
        total_farmers = User.objects.filter(farmer_profile__isnull=False).count()
        total_buyers = User.objects.filter(buyer_profile__isnull=False).count()
    
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    total_orders = Order.objects.count()
    
    # Recent activity
    recent_users = User.objects.order_by('-date_joined')[:10]
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]  # Fixed: using 'created' for Order model
    recent_products = Product.objects.select_related('farmer').order_by('-created_at')[:10]  # Fixed: using 'created_at' for Product model
    
    # Revenue statistics
    thirty_days_ago = timezone.now() - timedelta(days=30)
    monthly_revenue = Order.objects.filter(
        created_at__gte=thirty_days_ago,  # Fixed: using 'created' for Order model
        status='completed'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    total_revenue = Order.objects.filter(
        status='completed'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Pending orders that need attention
    pending_orders = Order.objects.filter(status='pending').count()
    
    # New users this month
    new_users = User.objects.filter(
        date_joined__gte=thirty_days_ago
    ).count()
    
    # Top selling products (based on order count)
    top_products = Product.objects.annotate(
        order_count=Count('created_at')
    ).order_by('-order_count')[:5]
    
    context = {
        'total_users': total_users,
        'total_farmers': total_farmers,
        'total_buyers': total_buyers,
        'total_products': total_products,
        'active_products': active_products,
        'total_orders': total_orders,
        'recent_users': recent_users,
        'recent_orders': recent_orders,
        'recent_products': recent_products,
        'monthly_revenue': monthly_revenue,
        'total_revenue': total_revenue,
        'pending_orders': pending_orders,
        'new_users': new_users,
        'top_products': top_products,
    }
    return render(request, 'accounts/admin_dashboard.html', context)


@login_required
def profile_setup(request):
    """Profile setup view for new users"""
    if request.method == 'POST':
        role = request.POST.get('role')
        
        if role == 'farmer':
            # Update user type or create farmer profile
            if hasattr(request.user, 'user_type'):
                request.user.user_type = 'farmer'
                request.user.save()
            
            # Create or get farmer profile if using profiles
            try:
                farmer_profile, created = FarmerProfile.objects.get_or_create(
                    user=request.user
                )
            except:
                pass
            
            messages.success(request, 'Farmer profile created successfully!')
            return redirect('accounts:farmer_dashboard')
            
        elif role == 'buyer':
            # Update user type or create buyer profile
            if hasattr(request.user, 'user_type'):
                request.user.user_type = 'buyer'
                request.user.save()
            
            # Create or get buyer profile if using profiles
            try:
                buyer_profile, created = BuyerProfile.objects.get_or_create(
                    user=request.user
                )
            except:
                pass
            
            messages.success(request, 'Buyer profile created successfully!')
            return redirect('accounts:buyer_dashboard')
    
    return render(request, 'accounts/profile_setup.html')


@login_required  
def switch_role(request):
    """Allow users to switch between farmer and buyer roles if they have both"""
    user = request.user
    current_role = request.session.get('current_role', 'farmer')
    
    if request.method == 'POST':
        new_role = request.POST.get('role')
        if new_role in ['farmer', 'buyer', 'admin']:
            # Check if user has the requested role
            if new_role == 'farmer' and (
                (hasattr(user, 'user_type') and user.user_type == 'farmer') or
                (hasattr(user, 'farmer_profile') and user.farmer_profile)
            ):
                request.session['current_role'] = 'farmer'
                return redirect('accounts:farmer_dashboard')
                
            elif new_role == 'buyer' and (
                (hasattr(user, 'user_type') and user.user_type == 'buyer') or
                (hasattr(user, 'buyer_profile') and user.buyer_profile)
            ):
                request.session['current_role'] = 'buyer'
                return redirect('accounts:buyer_dashboard')
                
            elif new_role == 'admin' and (user.is_staff or user.is_superuser):
                request.session['current_role'] = 'admin'
                return redirect('accounts:admin_dashboard')
    
    # Check what roles the user has
    has_farmer_profile = (
        (hasattr(user, 'user_type') and user.user_type == 'farmer') or
        (hasattr(user, 'farmer_profile') and user.farmer_profile)
    )
    has_buyer_profile = (
        (hasattr(user, 'user_type') and user.user_type == 'buyer') or
        (hasattr(user, 'buyer_profile') and user.buyer_profile)
    )
    has_admin_access = user.is_staff or user.is_superuser
    
    context = {
        'current_role': current_role,
        'has_farmer_profile': has_farmer_profile,
        'has_buyer_profile': has_buyer_profile,
        'has_admin_access': has_admin_access,
    }
    return render(request, 'accounts/switch_role.html', context)


@login_required
def dashboard_stats_api(request):
    """API endpoint for dashboard statistics (for AJAX updates)"""
    user = request.user
    stats = {}
    
    # Check if user is farmer
    if ((hasattr(user, 'user_type') and user.user_type == 'farmer') or
        (hasattr(user, 'farmer_profile') and user.farmer_profile)):
        
        products = Product.objects.filter(farmer=user)
        stats = {
            'total_products': products.count(),
            'active_products': products.filter(is_active=True).count(),
            'total_orders': Order.objects.filter(items__product__farmer=user).distinct().count(),
            'pending_orders': Order.objects.filter(
                items__product__farmer=user, 
                status='pending'
            ).distinct().count(),
        }
        
    # Check if user is buyer
    elif ((hasattr(user, 'user_type') and user.user_type == 'buyer') or
          (hasattr(user, 'buyer_profile') and user.buyer_profile)):
        
        orders = Order.objects.filter(user=user)
        stats = {
            'total_orders': orders.count(),
            'pending_orders': orders.filter(status='pending').count(),
            'completed_orders': orders.filter(status='completed').count(),
        }
    
    return JsonResponse(stats)