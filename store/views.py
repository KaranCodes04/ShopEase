from django.views.generic import ListView, DetailView
from .models import Product
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import CartItem
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect
from django.urls import reverse
from decimal import Decimal
from .models import Order, OrderItem

# Create your views here.

class ProductListView(ListView):
    model = Product
    template_name = 'store/product_list.html'
    context_object_name = 'products'

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

@login_required
def add_to_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('store:view_cart')

@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    cart_with_totals = []
    grand_total = 0
    for item in cart_items:
        line_total = item.product.price * item.quantity
        cart_with_totals.append((item, line_total))
        grand_total += line_total

    return render(request, 'store/cart.html', {
        'cart_with_totals': cart_with_totals,
        'grand_total': grand_total,
    })


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

@login_required
def checkout(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        address = request.POST.get('address')
        phone = request.POST.get('phone')

        cart_items = CartItem.objects.filter(user=request.user)
        if not cart_items.exists():
            return redirect('store:product_list')

        grand_total = 0
        for ci in cart_items:
            grand_total += ci.product.price * ci.quantity

        order = Order.objects.create(
            user=request.user,
            full_name=full_name,
            address=address,
            phone=phone,
            total=grand_total
        )

        for ci in cart_items:
            OrderItem.objects.create(
                order=order,
                product=ci.product,
                quantity=ci.quantity,
                price=ci.product.price
            )

        cart_items.delete()

        return redirect('store:checkout_success')

    cart_items = CartItem.objects.filter(user=request.user)
    cart_with_totals = []
    grand_total = 0
    for item in cart_items:
        line = item.product.price * item.quantity
        cart_with_totals.append((item, line))
        grand_total += line

    return render(request, 'store/checkout.html', {
        'cart_with_totals': cart_with_totals,
        'grand_total': grand_total
    })

@login_required
def checkout_success(request):
    return render(request, 'store/checkout_success.html')















