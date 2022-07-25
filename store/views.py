from django.shortcuts import redirect, render, get_object_or_404
from carts.models import CartItem
from carts.views import _cart_id

from category.models import Category
from orders.models import OrderProduct
from store.forms import ReviewForm
from .models import Product, ProductGallery, ReviewRating
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages


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
        in_cart = CartItem.objects.filter(
            cart__cart_id=_cart_id(request), product=single_product
        ).exists()
    except Exception as e:
        raise e
    if request.user.is_authenticated:
        try:
            order_product = OrderProduct.objects.filter(
                user=request.user, product_id=single_product.id
            ).exists()
        except OrderProduct.DoesNotExist:
            order_product = None
    else:
        order_product = None

    reviews = ReviewRating.objects.filter(product_id=single_product.id)

    product_gallery = ProductGallery.objects.filter(product__id=single_product.id)

    context = {
        "single_product": single_product,
        "in_cart": in_cart,
        "order_product": order_product,
        "reviews": reviews,
        "product_gallery": product_gallery,
    }

    return render(request, "store/product_detail.html", context)


def submit_review(request, product_id):
    url = request.META.get("HTTP_REFERER")
    if request.method == "POST":
        try:
            reviews = ReviewRating.objects.get(
                user__id=request.user.id, product__id=product_id
            )
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, "Thank you! Your review has been updated.")
            return redirect(url)

        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data["subject"]
                data.rating = form.cleaned_data["rating"]
                data.review = form.cleaned_data["review"]
                data.ip = request.META.get("REMOTE_ADDR")
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, "Thank you! Your review has been submitted.")
                return redirect(url)
