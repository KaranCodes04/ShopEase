from django.views.generic import ListView, DetailView
from .models import Product,Category
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CartItem
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect
from django.urls import reverse
from decimal import Decimal
from .models import Order, OrderItem
from django.contrib import messages
from django.http import JsonResponse
from django.db import models


# Create your views here.

class ProductListView(ListView):
    model = Product
    template_name = 'store/product_list.html'
    context_object_name = 'products'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.object.pk
        context['prev'] = Product.objects.filter(pk__lt=pk).order_by('-pk').first()
        context['next'] = Product.objects.filter(pk__gt=pk).order_by('pk').first()
        return context
    
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

@require_POST
def update_cart_item(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id, user=request.user)
    except CartItem.DoesNotExist:
        return HttpResponseRedirect(reverse('store:view_cart'))

    action = request.POST.get('action')
    if action == 'increment':
        cart_item.quantity += 1
        cart_item.save()
    elif action == 'decrement':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    return HttpResponseRedirect(reverse('store:view_cart'))

@require_POST
def remove_from_cart(request, item_id):
    CartItem.objects.filter(id=item_id, user=request.user).delete()
    return HttpResponseRedirect(reverse('store:view_cart'))




def about_view(request):
    return render(request, 'store/about.html')

def contact_view(request):
    return render(request, 'store/contact.html')


def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/orders.html', {'orders': orders})

def search(request):
    q = request.GET.get('q', '').strip()
    products = Product.objects.none()
    if q:
        products = Product.objects.filter(name__icontains=q) | Product.objects.filter(description__icontains=q)
    return render(request, 'store/product_list.html', {'products': products, 'categories': []})


def categories(request):
    categories = Category.objects.all()
    return render(request, 'store/categories.html', {'categories': categories})



from django.shortcuts import render, redirect, get_object_or_404
from .models import Product

def cart_view(request):
    cart = request.session.get('cart', {})

    # Handle quantity updates
    if request.method == 'POST':
        product_id = str(request.POST.get('product_id'))
        action = request.POST.get('action')
        if product_id in cart:
            if action == 'increase':
                cart[product_id] += 1
            elif action == 'decrease':
                cart[product_id] -= 1
                if cart[product_id] <= 0:
                    del cart[product_id]
        request.session['cart'] = cart
        return redirect('store:cart')

    products = []
    total = 0

    for product_id, quantity in cart.items():
        product = Product.objects.get(pk=product_id)
        subtotal = product.price * quantity
        products.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal
        })
        total += subtotal

    context = {
        'cart_items': products,
        'total': total
    }
    return render(request, 'store/cart.html', context)



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import CartItem, Product, Order, OrderItem

@login_required
def checkout(request):
    """
    Support both:
     - DB cart items (CartItem objects linked to request.user), and
     - session-based cart stored in request.session['cart'] as {product_id: quantity}
    """
    db_items = CartItem.objects.filter(user=request.user)
    session_cart = request.session.get('cart', {})

    if db_items.exists():
        cart_items = list(db_items) 
        total = sum(ci.subtotal for ci in cart_items)
        order = Order.objects.create(user=request.user, total=total)
        for ci in cart_items:
            OrderItem.objects.create(
                order=order,
                product=ci.product,
                quantity=ci.quantity,
                price=ci.product.price
            )
        db_items.delete()
    elif session_cart:
        items = []
        total = 0
        for pid_str, qty in session_cart.items():
            try:
                pid = int(pid_str)
                product = Product.objects.get(pk=pid)
            except (ValueError, Product.DoesNotExist):
                continue
            items.append((product, int(qty)))
            total += product.price * int(qty)

        if not items:
            messages.warning(request, "Your cart is empty.")
            return redirect('store:cart')

        order = Order.objects.create(user=request.user, total=total)
        for product, qty in items:
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=qty,
                price=product.price
            )

        request.session['cart'] = {}
        request.session.modified = True
    else:
        messages.warning(request, "Your cart is empty.")
        return redirect('store:cart')

    messages.success(request, "🎉 Order placed successfully!")
    return redirect('store:checkout_success')


@login_required
def checkout_success(request):
    return render(request, 'store/checkout_success.html')


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'store/order_detail.html', {'order': order})



@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/orders.html', {'orders': orders})


@login_required
def cart_view(request):
    items = CartItem.objects.filter(user=request.user).select_related('product')
    total = sum(item.subtotal for item in items)
    return render(request, 'store/cart.html', {'items': items, 'total': total})


@login_required
def update_cart_item(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("POST required")
    item_id = request.POST.get('item_id')
    action = request.POST.get('action')
    if not item_id or not action:
        return JsonResponse({'success': False})
    try:
        item = CartItem.objects.get(pk=item_id, user=request.user)
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False})

    if action == 'increase':
        item.quantity += 1
        item.save()
    elif action == 'decrease':
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
    elif action == 'remove':
        item.delete()
    else:
        return JsonResponse({'success': False})

    total = sum(ci.subtotal for ci in CartItem.objects.filter(user=request.user))
    return JsonResponse({'success': True, 'cart_count': CartItem.objects.filter(user=request.user).count(),
                         'total': float(total)})


@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('store:product_list')

    total = sum(item.subtotal for item in cart_items)

    order = Order.objects.create(user=request.user, total=total)
    for item in cart_items:
        OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity, price=item.product.price)

    cart_items.delete()  

    messages.success(request, "🎉 Order placed successfully!")
    return redirect('store:checkout_success')


@login_required
def checkout_success(request):
    return render(request, 'store/checkout_success.html')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from .models import Product, CartItem, Order, OrderItem


@login_required
def cart_view(request):
    items = CartItem.objects.filter(user=request.user).select_related('product')
    total = sum(item.subtotal for item in items)
    return render(request, 'store/cart.html', {'items': items, 'total': total})


@login_required
def update_cart_item(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("POST required")

    item_id = request.POST.get('item_id')
    action = request.POST.get('action')
    if not item_id or not action:
        return JsonResponse({'success': False})

    try:
        item = CartItem.objects.get(pk=item_id, user=request.user)
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False})

    if action == 'increase':
        item.quantity += 1
        item.save()
    elif action == 'decrease':
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
    elif action == 'remove':
        item.delete()
    else:
        return JsonResponse({'success': False})

    total = sum(ci.subtotal for ci in CartItem.objects.filter(user=request.user))
    return JsonResponse({
        'success': True,
        'cart_count': CartItem.objects.filter(user=request.user).count(),
        'total': float(total)
    })


@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('store:product_list')

    total = sum(item.subtotal for item in cart_items)

    order = Order.objects.create(user=request.user, total=total)
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price
        )

    cart_items.delete() 

    messages.success(request, "🎉 Order placed successfully!")
    return redirect('store:checkout_success')


@login_required
def checkout_success(request):
    return render(request, 'store/checkout_success.html')



from django.shortcuts import render, get_object_or_404
from .models import Category, Product

def category_list(request):
    categories = Category.objects.all()
    return render(request, 'store/categories.html', {'categories': categories})


import json
from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib import messages

from .models import Product, CartItem  

@require_POST
def add_to_cart(request, product_id):
    """
    Accepts JSON { "quantity": n } (or empty) and returns JSON response.
    Works for authenticated users (CartItem model) and guests (session cart).
    """
    try:
        payload = json.loads(request.body.decode('utf-8') or "{}")
    except Exception:
        payload = {}
    quantity = int(payload.get('quantity', 1) or 1)
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        item, created = CartItem.objects.get_or_create(user=request.user, product=product)
        if not created:
            item.quantity = item.quantity + quantity
        else:
            item.quantity = quantity
        item.save()

        cart_count = CartItem.objects.filter(user=request.user).count()
        return JsonResponse({
            "success": True,
            "message": f"{product.name} added to cart.",
            "cart_count": cart_count
        })

    cart = request.session.get('cart', {})
    pid = str(product_id)
    cart[pid] = cart.get(pid, 0) + quantity
    request.session['cart'] = cart
    cart_count = sum(int(v) for v in cart.values())
    return JsonResponse({
        "success": True,
        "message": f"{product.name} added to cart.",
        "cart_count": cart_count
    })


def view_cart(request):
    """
    Renders cart page. For authenticated users uses CartItem queryset.
    For guests uses session cart dict -> builds simple dict items list to render.
    The template expects `cart_items` where each item:
      - for auth: is a CartItem instance with .product, .quantity, .subtotal property
      - for guest: is a dict with keys: id (product.id), product (Product instance), quantity, subtotal
    """
    cart_items = []
    grand_total = Decimal('0.00')

    if request.user.is_authenticated:
        items = CartItem.objects.filter(user=request.user)
        for it in items:
            
            try:
                subtotal = it.product.price * it.quantity
            except Exception:
                subtotal = Decimal(it.quantity) * Decimal(it.product.price)
            grand_total += subtotal
        cart_items = items
    else:
        cart = request.session.get('cart', {})
        if cart:
            product_ids = [int(k) for k in cart.keys()]
            products = Product.objects.filter(id__in=product_ids)
            prod_map = {p.id: p for p in products}
            for pid_str, qty in cart.items():
                pid = int(pid_str)
                product = prod_map.get(pid)
                if not product:
                    continue
                subtotal = product.price * int(qty)
                cart_items.append({
                    'id': pid,             
                    'product': product,
                    'quantity': int(qty),
                    'subtotal': subtotal,
                })
                grand_total += subtotal

    context = {
        'cart_items': cart_items,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)


@require_POST
def cart_update(request, item_id):
    """
    Updates quantity.
    If user is authenticated, item_id is CartItem.id
    If guest, treat item_id as product_id in session cart.
    Expects JSON { "quantity": N }.
    Returns JSON with updated item_subtotal and grand_total.
    """
    try:
        payload = json.loads(request.body.decode('utf-8') or "{}")
    except Exception:
        payload = {}
    new_qty = int(payload.get('quantity', 0) or 0)


    if request.user.is_authenticated:
        item = get_object_or_404(CartItem, id=item_id, user=request.user)
        if new_qty < 1:
            item.delete()
        else:
            item.quantity = new_qty
            item.save()


        items = CartItem.objects.filter(user=request.user)
        grand_total = sum(i.product.price * i.quantity for i in items)
        item_subtotal = (item.product.price * item.quantity) if hasattr(item, 'product') else 0
        return JsonResponse({
            "success": True,
            "item_subtotal": float(item_subtotal),
            "grand_total": float(grand_total),
            "quantity": new_qty
        })

    pid = str(item_id)
    cart = request.session.get('cart', {})
    if pid not in cart:
        return JsonResponse({"success": False, "message": "Item not in cart."}, status=404)
    if new_qty < 1:
        cart.pop(pid, None)
    else:
        cart[pid] = new_qty
    request.session['cart'] = cart

    product_ids = [int(k) for k in cart.keys()]
    products = Product.objects.filter(id__in=product_ids)
    prod_map = {p.id: p for p in products}
    grand_total = 0
    for k, q in cart.items():
        p = prod_map.get(int(k))
        if p:
            grand_total += p.price * int(q)
    item_subtotal = 0
    p = prod_map.get(int(pid))
    if p and pid in cart:
        item_subtotal = p.price * int(cart[pid])
    return JsonResponse({
        "success": True,
        "item_subtotal": float(item_subtotal),
        "grand_total": float(grand_total),
        "quantity": new_qty
    })

@require_POST
def cart_remove(request, item_id):
    """
    Remove an item. If user is authenticated, item_id is CartItem.id.
    If guest, item_id is product id to remove from session cart.
    Returns JSON { success, grand_total }.
    """
    if request.user.is_authenticated:
        item = get_object_or_404(CartItem, id=item_id, user=request.user)
        item.delete()
        items = CartItem.objects.filter(user=request.user)
        grand_total = sum(i.product.price * i.quantity for i in items)
        return JsonResponse({"success": True, "grand_total": float(grand_total)})
    else:
        pid = str(item_id)
        cart = request.session.get('cart', {})
        if pid in cart:
            cart.pop(pid)
            request.session['cart'] = cart
        product_ids = [int(k) for k in cart.keys()]
        products = Product.objects.filter(id__in=product_ids)
        grand_total = 0
        for p in products:
            grand_total += p.price * cart.get(str(p.id), 0)
        return JsonResponse({"success": True, "grand_total": float(grand_total)})

from django.shortcuts import render, get_object_or_404
from .models import Product, Category  

def product_list(request):
    """
    Show all products. Provide 'categories' and 'selected_category' = None
    so the category bar in the template can render.
    """
    products = Product.objects.all().order_by('id') 
    categories = Category.objects.all()
    context = {
        'products': products,
        'categories': categories,
        'selected_category': None,
    }
    return render(request, 'store/product_list.html', context)


def products_by_category(request, pk):
    """
    Show products filtered by category id (pk).
    Provide the categories list and the selected_category object.
    """
    category = get_object_or_404(Category, id=pk)
    products = Product.objects.filter(category=category).order_by('id')
    categories = Category.objects.all()
    context = {
        'products': products,
        'categories': categories,
        'selected_category': category,
    }
    return render(request, 'store/product_list.html', context)





