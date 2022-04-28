from django.shortcuts import render
from store.models import Product


def home(request):
    products = (
        Product.objects.select_related("category")
        .all()
        .filter(is_aviable=True)
        .only('id', 'slug', 'category__id', "product_name", 'category__slug', "images", "price", )
    )

    context = {
        "products": products,
    }
    return render(request, "home.html", context)
