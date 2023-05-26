from django.shortcuts import render, redirect
from carts.models import CartItem
from .forms import OrderForm, Order
import datetime
from .models import Order, Payment, Account, OrderProduct, Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

tax_rate=stripe.TaxRate.create(
  display_name="Sales Tax",
  inclusive=False,
  percentage=2.00,
)

 
# Create your views here.
def charges(request, order_id):
  try:
    cart_items = CartItem.objects.filter(user=request.user)
    domain = "https://yourdomain.com/"
    if settings.DEBUG:
      domain = "http://127.0.0.1:8000/"   
    session = stripe.checkout.Session.create(
      customer_email=request.user.email,
      payment_method_types=['card'],
      line_items=[{
        'price_data': {
          'product_data': {
            'name': cart_item.product.product_name,
          },
          'unit_amount': cart_item.product.price*100,
          'currency': 'usd',
        },
        'quantity': cart_item.quantity,
        'tax_rates': [tax_rate.id],
      } for cart_item in cart_items],
      metadata={
         "orderID": order_id
      },
      mode='payment',
      success_url=domain + 'orders/order_complete?session_id={CHECKOUT_SESSION_ID}',
      cancel_url=domain + 'orders/order_incomplete?session_id={CHECKOUT_SESSION_ID}',
    )
  
    # Pass the session ID to the template
    return JsonResponse({
       "id": session.id
    })
  except stripe.error.InvalidRequestError as e:
    # Handle the specific InvalidRequestError exception
    print(f"Invalid request error: {e.param}")
  except stripe.error.StripeError as e:
    # Handle other Stripe-related errors
    print(f"Stripe error: {e}")
  except stripe.error.ValueError as e:
    print(f"Stripe error: {e}")
    print(e.error)
  except Exception as e:
    # Handle other general exceptions
    return JsonResponse({'error': str(e)}) 
  

@csrf_exempt
def stripe_webhook(request):
  payload = request.body
  sig_header = request.META['HTTP_STRIPE_SIGNATURE']
  event = None

  try:
    event = stripe.Webhook.construct_event(
      payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
    )
  except ValueError as e:
    # Invalid payload
    print(f"Error: {e}")
    return HttpResponse(status=400)
  except stripe.error.SignatureVerificationError as e:
    # Invalid signature
    print(f"Error: {e}")
    return HttpResponse(status=400)

  if event['type'] == 'checkout.session.completed':
  # Retrieve the session. If you require line items in the response, you may include them by expanding line_items.
    session = event['data']['object']

    order_number = session["metadata"]["orderID"]
    payment_id = session["id"]
    payment_method = session["payment_method_types"][0]
    status = session["status"]
    customer_email = session["customer_details"]["email"]

    request.user = Account.objects.get(email=customer_email)
    payments(request, payment_id, payment_method, status, order_number)

  # Passed signature verification
  return HttpResponse(status=200)


def payments(request, payment_id, payment_method, status, order_number):
  current_user = request.user
  try:
    order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
    
    payment = Payment(
      user = current_user,
      payment_id = payment_id,
      payment_method = payment_method,
      amount_paid = order.order_total,
      status = status,
    )
    payment.save()

    order.payment = payment
    order.is_ordered = True
    order.save()

    # Move the cart items to Order Product Table
    cart_items = CartItem.objects.filter(user=current_user)

    for item in cart_items:
      orderproduct = OrderProduct()
      orderproduct.order_id = order.id
      orderproduct.payment = payment
      orderproduct.user_id = request.user.id
      orderproduct.product_id = item.product_id
      orderproduct.quantity = item.quantity
      orderproduct.product_price = item.product.price
      orderproduct.ordered = True
      orderproduct.save()

      cart_item = CartItem.objects.get(id=item.id)
      product_variation = cart_item.variations.all()
      orderproduct = OrderProduct.objects.get(id=orderproduct.id)
      orderproduct.variations.set(product_variation)
      orderproduct.save()

      # Reduce the quantity of the sold products
      product = Product.objects.get(id=item.product_id)
      product.stock -= item.quantity
      product.save()

    # Clear cart
    CartItem.objects.filter(user=current_user).delete()

    # Send order received email to customer
    mail_subject = "Thank you for your order!"
    message = render_to_string('orders/order_received_email.html',{
        "user": current_user,
        "order": order,
    })
    to_email = current_user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()

    # Send order number and transaction id back to 
  except ValueError as e:
      print(f"ValueError: {e}")


def place_order(request, total=0, quantity=0):
    current_user = request.user

    # If the cart count is less than or equal to 0, then redirect back to shop
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect("store")
    
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total) / 100
    grand_total = total + tax
    grand_total = f'{grand_total:.2f}'
    
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            # Store all the billing information inside Order table
            data = Order()
            data.user = current_user
            data.full_name = form.cleaned_data["full_name"]
            data.address_line_1 = form.cleaned_data["address_line_1"]
            data.address_line_2 = form.cleaned_data["address_line_2"]
            data.city = form.cleaned_data["city"]
            data.state = form.cleaned_data["state"]
            data.zip = form.cleaned_data["zip"]
            data.phone = form.cleaned_data["phone"]
            data.delivery_note = form.cleaned_data["delivery_note"]
            data.country = form.cleaned_data["country"]
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get("REMOTE_ADDR")
            data.save()
            # Generate order number
            yr = int(datetime.date.today().strftime("%Y"))
            dt = int(datetime.date.today().strftime("%d"))
            mt = int(datetime.date.today().strftime("%m"))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%m%d%Y")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            
            stripe_pk = settings.STRIPE_PUBLIC_KEY
            stripe_total = grand_total*100
            stripe_email = current_user.email

            context = {
                "order": order,
                "cart_items": cart_items,
                "total": total,
                "tax": tax,
                "grand_total": grand_total,
                "stripe_total": stripe_total,
                "stripe_public_key": stripe_pk,
                "stripe_email": stripe_email,
            }

            return render(request, "orders/payments.html", context)
        
    else:
        return redirect("checkout") 
    

def order_complete(request):
   session_id = request.GET.get('session_id')
   session = stripe.checkout.Session.retrieve(session_id)
   order_number = session["metadata"]["orderID"]
   transID = session["id"]

   try:
      order = Order.objects.get(order_number=order_number, is_ordered=True)
      ordered_products = OrderProduct.objects.filter(order_id=order.id)

      subtotal = 0
      for i in ordered_products:
          subtotal += i.product_price * i.quantity

      subtotal = format(subtotal, ".2f")
      tax = format(order.tax, ".2f")
      order_total = format(order.order_total, ".2f")

      payment = Payment.objects.get(payment_id=transID)

      context = {
          'order': order,
          'ordered_products': ordered_products,
          'order_number': order.order_number,
          'transID': payment.payment_id,
          'payment': payment,
          'subtotal': subtotal,
          "tax": tax,
          "order_total": order_total
      }
      return render(request, "orders/order_complete.html", context)
   except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')
  
def order_incomplete(request):
  return render(request, "orders/order_incomplete.html")
   