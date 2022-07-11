import datetime
import json
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from carts.models import CartItem
from orders.models import Order, OrderProduct, Payment
from store.models import Product
from .forms import OrderForm

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
import requests


def custom_redirect(url_name, *args, **kwargs):
    from django.urls import reverse
    import urllib

    url = reverse(url_name, args=args)
    params = urllib.parse.urlencode(kwargs)
    return HttpResponseRedirect(url + "?%s" % params)


def place_order(request, total=0, quantity=0, grand_total=0, tax=0):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect("store")

    for cart_item in cart_items:
        total += cart_item.product.price * cart_item.quantity
        quantity += cart_item.quantity
    tax = (2 * total) / 100
    grand_total = total + tax
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data["first_name"]
            data.last_name = form.cleaned_data["last_name"]
            data.phone = form.cleaned_data["phone"]
            data.email = form.cleaned_data["email"]
            data.address_line_1 = form.cleaned_data["address_line_1"]
            data.address_line_2 = form.cleaned_data["address_line_2"]
            data.country = form.cleaned_data["country"]
            data.state = form.cleaned_data["state"]
            data.city = form.cleaned_data["city"]
            data.order_note = form.cleaned_data["order_note"]
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get("REMOTE_ADDR")
            data.save()
            yr = int(datetime.date.today().strftime("%Y"))
            dt = int(datetime.date.today().strftime("%d"))
            mt = int(datetime.date.today().strftime("%m"))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(
                user=current_user, is_ordered=False, order_number=order_number
            )

            context = {
                "order": order,
                "cart_items": cart_items,
                "total": total,
                "tax": tax,
                "grand_total": grand_total,
            }
            return render(request, "orders/payments.html", context)

        else:
            return redirect("checkout")
    else:
        return redirect("checkout")


def payments(request):

    # body = json.loads(request.body)
    # order = Order.objects.get(
    #     user=request.user, is_ordered=False, order_number=body["orderID"]
    # )
    # payment = Payment(
    #     user=request.user,
    #     payment_id=body["transactionID"],
    #     payment_method=body["transactionID"],
    #     amount_paid=order.order_total,
    #     status=body["status"],
    # )
    # payment.save()
    # order.payment = payment
    # order.is_ordered = True
    # order.save()

    latest_order = Order.objects.latest("id").order_number
    order = get_object_or_404(
        Order,
        user=request.user,
        is_ordered=False,
        order_number=latest_order,
    )

    payment = Payment(
        user=request.user,
        payment_id=f"ORDERID{order.id}",
        payment_method="PayPal",
        amount_paid=order.order_total,
        status="SUCCESS",
    )
    payment.save()

    order.payment = payment
    order.is_ordered = True
    order.save()

    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        order_product = OrderProduct()
        order_product.order_id = order.id
        order_product.payment = payment
        order_product.user_id = request.user.id
        order_product.product_id = item.product_id
        order_product.quantity = item.quantity
        order_product.product_price = item.product.price
        order_product.ordered = True
        order_product.save()

        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        order_product = OrderProduct.objects.get(id=order_product.id)
        order_product.variations.set(product_variation)
        order_product.save()

        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    CartItem.objects.filter(user=request.user).delete()

    mail_subject = "Thank you for order!"
    message = render_to_string(
        "orders/order_recieved_mail.html",
        {
            "user": request.user,
            "order": order,
        },
    )
    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, from_email="noreply@gmail.com", to=[to_email])
    send_email.send()

    data = {
        "order_number": order.order_number,
        "transactionID": payment.payment_id,
    }
    return custom_redirect(
        "order_complite",
        order_number=data["order_number"],
        transactionID=data["transactionID"],
    )


def order_complite(request):
    order_number = request.GET.get("order_number")
    transactionID = request.GET.get("transactionID")
    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        payment = Payment.objects.get(payment_id=transactionID)

        sub_total = order.order_total - order.tax

        context = {
            "order": order,
            "ordered_products": ordered_products,
            "transactionID": payment.payment_id,
            "payment": payment,
            "sub_total": sub_total,
        }
        return render(request, "orders/order_complite.html", context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect("home")
