from django.db import models
from accounts.models import Account
from store.models import Product, Variation
from localflavor.us.models import USStateField, USZipCodeField
from django.core.validators import RegexValidator
from localflavor.us.us_states import US_STATES


# Create your models here.
class Payment(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100) # stripe_checkout_id
    payment_method = models.CharField(max_length=100)
    amount_paid = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.payment_id
    

class Order(models.Model):
    STATUS = (
        ("open", "open"),
        ("complete", "complete"),
        ("expired", "expired"),
    )
    COUNTRY = (
        ("US", "United States of America"),
    )

    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    order_number = models.CharField(max_length=20)
    country = models.CharField(max_length=2, choices=COUNTRY)
    full_name = models.CharField(max_length=50)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True) # Validators should be a list
    address_line_1 = models.CharField(max_length=50)
    address_line_2 = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50)
    state = USStateField(choices=US_STATES)
    zip = USZipCodeField(default="XXXXX")
    delivery_note = models.CharField(max_length=100, blank=True)
    order_total = models.DecimalField(max_digits=19, decimal_places=2)
    sub_total = models.DecimalField(max_digits=19, decimal_places=2)
    tax = models.DecimalField(max_digits=19, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS, default="open")
    ip = models.CharField(blank=True, max_length=20)
    is_ordered = models.BooleanField(default=False) # payment_bool
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def full_address(self):
        return f"{self.address_line_1} {self.address_line_2}"

    def __str__(self):
        return self.full_name
    


class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variations = models.ManyToManyField(Variation,blank=True)
    quantity = models.IntegerField()
    product_price = models.DecimalField(max_digits=19, decimal_places=2)
    ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product.product_name