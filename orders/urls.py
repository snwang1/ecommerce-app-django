from django.urls import path
from . import views

urlpatterns=[
    path("place_order/", views.place_order, name="place_order"),
    path("payments/", views.payments, name="payments"),
    path("charges/<order_id>/", views.charges, name="charges"),
    path("stripe_webhook/", views.stripe_webhook, name="stripe_webhook"),
    path("order_complete/", views.order_complete, name="order_complete"),
    path("order_incomplete/", views.order_incomplete, name="order_incomplete"),
]