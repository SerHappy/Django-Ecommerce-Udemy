import re
from django.shortcuts import redirect, render, get_object_or_404
from .models import Cart, CartItem
from store.models import Product, Variation
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def add_cart(request, product_id):
    current_user = request.user
    product = get_object_or_404(Product, id=product_id)
    if current_user.is_authenticated:
        product_variation = []
        if request.method == "POST":
            for item in request.POST:
                key = item
                value = request.POST[key]
                try:
                    variation = Variation.objects.get(
                        variation_category__iexact=key, variation_value__iexact=value
                    )
                    product_variation.append(variation)
                except:
                    pass
        is_cart_item_exists = CartItem.objects.filter(
            product=product, user=current_user
        ).exists()
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(
                product=product,
                user=current_user,
            )
            ex_var_list = []
            id = []
            for item in cart_item:
                existing_vatiarion = item.variations.all()
                ex_var_list.append(list(existing_vatiarion))
                id.append(item.id)

            if product_variation in ex_var_list:
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()
            else:
                cart_item = CartItem.objects.create(
                    product=product,
                    quantity=1,
                    user=current_user,
                )
                if len(product_variation) > 0:
                    cart_item.variations.clear()
                    cart_item.variations.add(*product_variation)
        else:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                user=current_user,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
        return redirect("cart")
    else:
        product_variation = []
        if request.method == "POST":
            for item in request.POST:
                key = item
                value = request.POST[key]
                try:
                    variation = Variation.objects.get(
                        variation_category__iexact=key, variation_value__iexact=value
                    )
                    product_variation.append(variation)
                except:
                    pass
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()

        is_cart_item_exists = CartItem.objects.filter(
            product=product, cart=cart
        ).exists()
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(
                product=product,
                cart=cart,
            )
            ex_var_list = []
            id = []
            for item in cart_item:
                existing_vatiarion = item.variations.all()
                ex_var_list.append(list(existing_vatiarion))
                id.append(item.id)

            if product_variation in ex_var_list:
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()
            else:
                cart_item = CartItem.objects.create(
                    product=product,
                    quantity=1,
                    cart=cart,
                )
                if len(product_variation) > 0:
                    cart_item.variations.clear()
                    cart_item.variations.add(*product_variation)
        else:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                cart=cart,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
        return redirect("cart")


def remove_cart_item(request, product_id, cart_item_id):

    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(
            product=product, user=request.user, id=cart_item_id
        )
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    cart_item.delete()
    return redirect("cart")


def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item = get_object_or_404(
            CartItem, product=product, user=request.user, id=cart_item_id
        )
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = get_object_or_404(Cart, product=product, cart=cart, id=cart_item_id)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect("cart")


def cart(request, total=0, grand_total=0, tax=0, quantity=0, cart_items=None):
    try:
        if request.user.is_authenticated:
            cart_items = (
                CartItem.objects.select_related("product__category")
                .prefetch_related(
                    Prefetch(
                        "variations",
                        queryset=Variation.objects.all().only(
                            "variation_category", "variation_value"
                        ),
                    )
                )
                .filter(user=request.user, is_active=True)
                .only(
                    "product__product_name",
                    "product__price",
                    "quantity",
                    "product__category__slug",
                    "product__images",
                    "product__slug",
                    "is_active",
                )
            )
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = (
                CartItem.objects.select_related("product__category")
                .prefetch_related(
                    Prefetch(
                        "variations",
                        queryset=Variation.objects.all().only(
                            "variation_category", "variation_value"
                        ),
                    )
                )
                .filter(cart=cart, is_active=True)
                .only(
                    "product__product_name",
                    "product__price",
                    "quantity",
                    "product__category__slug",
                    "product__images",
                    "product__slug",
                    "is_active",
                )
            )
        for cart_item in cart_items:
            total += cart_item.product.price * cart_item.quantity
            quantity += cart_item.quantity
        tax = (2 * total) / 100
        grand_total = total + tax
    except Cart.DoesNotExist:
        cart = Cart.objects.create(cart_id=_cart_id(request))

    context = {
        "cart_items": cart_items,
        "total": total,
        "quantity": quantity,
        "tax": tax,
        "grand_total": grand_total,
    }
    return render(request, "store/cart.html", context)


@login_required(login_url="login")
def checkout(request, total=0, grand_total=0, tax=0, quantity=0, cart_items=None):
    cart_items = (
        CartItem.objects.select_related("product__category")
        .prefetch_related(
            Prefetch(
                "variations",
                queryset=Variation.objects.all().only(
                    "variation_category", "variation_value"
                ),
            )
        )
        .filter(user=request.user, is_active=True)
        .only(
            "product__product_name",
            "product__price",
            "quantity",
            "product__category__slug",
            "product__images",
            "product__slug",
            "is_active",
        )
    )
    for cart_item in cart_items:
        total += cart_item.product.price * cart_item.quantity
        quantity += cart_item.quantity
    tax = (2 * total) / 100
    grand_total = total + tax

    context = {
        "cart_items": cart_items,
        "total": total,
        "quantity": quantity,
        "tax": tax,
        "grand_total": grand_total,
    }
    return render(request, "store/checkout.html", context)
