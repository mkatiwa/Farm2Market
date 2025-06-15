from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse
from products.models import Product
from .cart import Cart
from .forms import CartAddProductForm

def cart_detail(request):
    cart = Cart(request)
    
    # Calculate cart totals
    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(
            initial={'quantity': item['quantity'], 'override': True}
        )
    
    context = {
        'cart': cart,
    }
    return render(request, 'cart/cart_detail.html', context)

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)
    
    if form.is_valid():
        cd = form.cleaned_data
        quantity = cd['quantity']
        
        # Check if enough stock is available
        if product.stock < quantity:
            messages.error(request, f'Only {product.stock} items available in stock.')
            return redirect('products:product_detail', slug=product.slug)
        
        cart.add(
            product=product,
            quantity=quantity,
            override_quantity=cd['override']
        )
        messages.success(request, f'{product.name} added to cart.')
    
    return redirect('cart:cart_detail')

@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.success(request, f'{product.name} removed from cart.')
    return redirect('cart:cart_detail')

@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)
    
    if form.is_valid():
        cd = form.cleaned_data
        quantity = cd['quantity']
        
        if quantity > 0:
            # Check stock availability
            if product.stock < quantity:
                messages.error(request, f'Only {product.stock} items available in stock.')
                return redirect('cart:cart_detail')
            
            cart.add(product=product, quantity=quantity, override_quantity=True)
            messages.success(request, 'Cart updated successfully.')
        else:
            cart.remove(product)
            messages.success(request, f'{product.name} removed from cart.')
    
    return redirect('cart:cart_detail')

def cart_clear(request):
    cart = Cart(request)
    cart.clear()
    messages.success(request, 'Cart cleared successfully.')
    return redirect('cart:cart_detail')

# AJAX view for updating cart
def cart_update_ajax(request, product_id):
    if request.method == 'POST':
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity > 0:
            if product.stock < quantity:
                return JsonResponse({
                    'success': False, 
                    'message': f'Only {product.stock} items available in stock.'
                })
            
            cart.add(product=product, quantity=quantity, override_quantity=True)
        else:
            cart.remove(product)
        
        return JsonResponse({
            'success': True,
            'cart_total': str(cart.get_total_price()),
            'cart_length': len(cart),
            'item_total': str(cart.cart[str(product_id)]['total_price']) if str(product_id) in cart.cart else '0'
        })
    
    return JsonResponse({'success': False})


# cart/context_processors.py
from .cart import Cart

def cart(request):
    return {'cart': Cart(request)}

# Add this to your settings.py - CART_SESSION_ID
# settings.py (add this line)
CART_SESSION_ID = 'cart'