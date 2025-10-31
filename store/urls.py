from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'store'

urlpatterns = [
    path('product/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('', views.product_list, name='product_list'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'),
    path('cart/', views.view_cart, name='cart'),

    path('checkout/', views.checkout, name='checkout'),
    path('checkout/success/', views.checkout_success, name='checkout_success'),

    path('category/<int:pk>/', views.products_by_category, name='products_by_category'),
    path('categories/', views.category_list, name='categories'),

    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),

    path('my-orders/', views.my_orders, name='my_orders'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),

    path('search/', views.search, name='search'),

    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

]




