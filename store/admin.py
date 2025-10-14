from django.contrib import admin

# Register your models here.

from .models import Category, Product

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'created_at')

admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
