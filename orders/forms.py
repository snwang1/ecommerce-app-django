from django import forms
from .models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["country","full_name", "address_line_1", "address_line_2", "city", "state", "zip", "phone", "delivery_note"]