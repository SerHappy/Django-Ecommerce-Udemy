from django.shortcuts import render, get_object_or_404

from category.models import Category
from .models import Product
from django.core.paginator import Paginator
from django.db.models import Q


def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = (
            Product.objects.select_related("category")
            .filter(category=categories, is_aviable=True)
            .order_by("id")
        )
        pagitaor = Paginator(products, 1)
        page_number = request.GET.get("page")
        page_obj = pagitaor.get_page(page_number)
    else:
        products = (
            Product.objects.select_related("category")
            .filter(is_aviable=True)
            .order_by("id")
        )
        pagitaor = Paginator(products, 1)
        page_number = request.GET.get("page")
        page_obj = pagitaor.get_page(page_number)

    context = {
        "products": page_obj,
        "products_count": page_obj.count,
    }
    return render(request, "store/store.html", context)


def search(request):
    if "keyword" in request.GET:
        keyword = request.GET["keyword"]
        if keyword:
            products = (
                Product.objects.select_related("category")
                .order_by("-created_date")
                .filter(
                    Q(description__icontains=keyword)
                    | Q(product_name__icontains=keyword)
                )
            )
            products_count = products.count()
    context = {
        "products": products,
        "products_count": products_count,
    }
    return render(request, "store/store.html", context)


def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(
            category__slug=category_slug, slug=product_slug
        )
    except Exception as e:
        raise e
    context = {
        "single_product": single_product,
    }

    return render(request, "store/product_detail.html", context)
