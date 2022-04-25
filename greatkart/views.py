from django.shortcuts import render
from store.models import Product


def home(request):
    products = Product.objects.select_related('category').all().filter(is_aviable=True)

    context = {
        "products": products,
    }
    return render(request, "home.html", context)
