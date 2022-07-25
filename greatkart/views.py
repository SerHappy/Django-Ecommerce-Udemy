from django.shortcuts import render
from store.models import Product, ReviewRating


def home(request):
    products = (
        Product.objects.select_related("category")
        .all()
        .filter(is_aviable=True)
        .only(
            "id",
            "slug",
            "category__id",
            "product_name",
            "category__slug",
            "images",
            "price",
        )
        .order_by("created_date")
    )
    for single_product in products:
        reviews = ReviewRating.objects.filter(product_id=single_product, status=True)

    context = {
        "products": products,
        "reviews": reviews,
    }
    return render(request, "home.html", context)
