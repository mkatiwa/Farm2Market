# products/views.py
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Product, Category

def product_list(request):
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.all()
    
    # Filter by category
    category = request.GET.get('category')
    if category:
        products = products.filter(category__slug=category)
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        products = products.filter(name__icontains=search)
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': products,  # Add this for the template
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category,
        'search_query': search,
    }
    return render(request, 'products/product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    # Fixed template path
    return render(request, 'products/product_detail.html', context)

def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category, is_active=True)
    
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'products/category_detail.html', context)