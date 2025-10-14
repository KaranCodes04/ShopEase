from django.views.generic import ListView, DetailView
from .models import Product

# Create your views here.

class ProductListView(ListView):
    model = Product
    template_name = 'product_list.html'
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














