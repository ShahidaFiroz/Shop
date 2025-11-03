from django.db import models
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.category.name} - {self.name}"


# class Product(models.Model):
#     subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE)
#     name = models.CharField(max_length=150)
#     image = models.ImageField(upload_to='products/', null=True, blank=True)
#     stock = models.IntegerField(default=0)
#     purchase_price = models.FloatField()
#     sale_price = models.FloatField()

#     def __str__(self):
#         return self.name
from django.db import models

class Product(models.Model):
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    stock = models.IntegerField(default=0)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)  # ✅ was FloatField
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)      # ✅ was FloatField

    def __str__(self):
        return self.name


# class Vendor(models.Model):
#     name = models.CharField(max_length=150)
#     phone = models.CharField(max_length=15, blank=True)
#     balance = models.FloatField(default=0.0)

#     def __str__(self):
#         return self.name

# class Vendor(models.Model):
#     name = models.CharField(max_length=150)
#     phone = models.CharField(max_length=15, blank=True)
#     balance = models.FloatField(default=0.0)

#     def __str__(self):
#         return self.name

#     def pending_total(self):
#         total_pending = sum(p.total_price - sum(pay.amount for pay in p.vendor.payments.all()) 
#                             for p in self.purchases.all())
#         return total_pending
from django.db import models
from decimal import Decimal


# class Vendor(models.Model):
#     name = models.CharField(max_length=150)
#     phone = models.CharField(max_length=15, blank=True)
#     balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
#     opening_balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

#     def __str__(self):
#         return self.name

#     def pending_total(self):
#         # Safely calculate totals using Decimal
#         total_purchases = sum(p.total_price for p in self.purchases.all())
#         total_payments = sum(pay.amount for pay in self.payments.all())
#         return total_purchases - total_payments

#     def update_balance(self):
#         """Recalculate and store the current vendor balance."""
#         new_balance = self.pending_total()
#         if new_balance is None:
#             new_balance = Decimal('0.00')
#         self.balance = new_balance
#         self.save(update_fields=['balance'])

class Vendor(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15, blank=True)
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return self.name

    def pending_total(self):
        """Return total pending including opening balance."""
        total_purchases = sum(p.total_price for p in self.purchases.all())
        total_payments = sum(pay.amount for pay in self.payments.all())
        return self.opening_balance + total_purchases - total_payments

    def update_balance(self):
        """Recalculate vendor’s live balance."""
        self.balance = self.pending_total()
        self.save(update_fields=['balance'])

# class Purchase(models.Model):
#     vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     quantity = models.IntegerField()
#     price = models.FloatField()
#     total_price = models.FloatField(blank=True, null=True)
#     date = models.DateField(default=timezone.now)

#     def __str__(self):
#         return f"Purchase {self.id} - {self.vendor.name}"

# class Purchase(models.Model):
#     vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='purchases')
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     quantity = models.IntegerField()
#     price = models.FloatField()
#     total_price = models.FloatField(blank=True, null=True)
#     date = models.DateField(default=timezone.now)

#     def save(self, *args, **kwargs):
#         self.total_price = self.quantity * self.price
#         super().save(*args, **kwargs)

#     def pending_amount(self):
#         paid = sum(p.amount for p in self.vendor.payments.all())
#         return self.total_price - paid

from decimal import Decimal

class Purchase(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='purchases')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    date = models.DateField(default=timezone.now)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.price
        super().save(*args, **kwargs)

        # Create payment if part paid
        if self.amount_paid > 0:
            Payment.objects.create(
                vendor=self.vendor,
                purchase=self,
                amount=self.amount_paid,
                date=self.date
            )

        # ✅ Now update the vendor’s balance
        self.vendor.update_balance()
   
# class Payment(models.Model):
#     vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
#     amount = models.FloatField()
#     date = models.DateField(default=timezone.now)

#     def __str__(self):
#         return f"Payment {self.vendor.name} - {self.amount}"

class Payment(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='payments')
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, null=True, blank=True, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # ✅ DecimalField
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Payment {self.vendor.name} - {self.amount}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update vendor balance automatically after saving a payment
        self.vendor.update_balance()


from django.utils import timezone

class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    date = models.DateTimeField(default=timezone.now)  # ✅ instead of auto_now_add

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.price
        if not self.date:
            self.date = timezone.now()
        super().save(*args, **kwargs)
