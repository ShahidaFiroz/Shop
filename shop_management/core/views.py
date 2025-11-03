from datetime import datetime, timedelta, date
from decimal import Decimal
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone

from .models import Product, Category, SubCategory, Vendor, Sale, Purchase, Payment
from .forms import ProductForm, VendorForm, PurchaseForm, SaleForm, PaymentForm

# -----------------------
# Authentication Views
# -----------------------
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password")
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# 🏠 Dashboard View
# @login_required
# def dashboard(request):
#     total_sales = 0
#     total_purchase = 0
#     profit = 0

#     try:
#         sales = Sale.objects.all()
#         purchases = Purchase.objects.all()

#         # Only use numeric totals, ignore broken date rows
#         total_sales = sum(float(s.total_price or 0) for s in sales)
#         total_purchase = sum(float(p.total_price or 0) for p in purchases)
#         profit = total_sales - total_purchase

#     except Exception as e:
#         print("⚠️ Dashboard date error:", e)

#     low_stock = Product.objects.filter(stock__lte=5)

#     vendors = Vendor.objects.all()
#     for vendor in vendors:
#         total_purchase_amount = (
#             Purchase.objects.filter(vendor=vendor).aggregate(total=Sum('total_price'))['total'] or 0
#         )
#         total_paid = (
#             Payment.objects.filter(vendor=vendor).aggregate(total=Sum('amount'))['total'] or 0
#         )
#         vendor.pending_total = total_purchase_amount - total_paid

#     return render(request, 'core/dashboard.html', {
#         'total_sales': total_sales,
#         'total_purchase': total_purchase,
#         'profit': profit,
#         'low_stock': low_stock,
#         'vendors': vendors,
#     })



# views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from .models import Sale, Purchase, Product


from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from .models import Sale, Purchase, Vendor, Product
@login_required

def dashboard(request):
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)

    # --- Date Filtering ---
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    sales_queryset = Sale.objects.all()
    purchases_queryset = Purchase.objects.all()

    if start_date and end_date:
        sales_queryset = sales_queryset.filter(date__date__range=[start_date, end_date])
        purchases_queryset = purchases_queryset.filter(date__range=[start_date, end_date])

    # --- Totals ---
    total_sales = sales_queryset.aggregate(total=Sum('total_price'))['total'] or 0
    total_purchase = purchases_queryset.aggregate(total=Sum('total_price'))['total'] or 0
    # Actual profit: (selling price - product purchase price) * quantity
    total_profit = sum(
        (sale.price - sale.product.purchase_price) * sale.quantity
        for sale in sales_queryset
    )
     # Today and Yesterday sales count
    today = date.today()
    yesterday = today - timedelta(days=1)
    today_sales_count = Sale.objects.filter(date__date=today).count()
    yesterday_sales_count = Sale.objects.filter(date__date=yesterday).count()

    # Low stock products
    low_stock = Product.objects.filter(stock__lte=5)  # example threshold

    # --- Vendor Pending Amounts ---
    vendors = Vendor.objects.all()
    for vendor in vendors:
        vendor.pending_total = sum(
            p.total_price - sum(payment.amount for payment in p.payments.all())
            for p in vendor.purchases.all()
        )

    # --- Charts Data (Last 7 days) ---
    chart_labels = []
    sales_values = []
    profit_values = []

    for i in range(6, -1, -1):  # last 7 days
     day = today - timedelta(days=i)
    
    day_sales = Sale.objects.filter(date__date=day)
    total_day_sales = day_sales.aggregate(total=Sum('total_price'))['total'] or 0
    total_day_purchase = Purchase.objects.filter(date=day).aggregate(total=Sum('total_price'))['total'] or 0
    total_day_profit = total_day_sales - total_day_purchase

    chart_labels.append(day.strftime('%b %d'))
    sales_values.append(total_day_sales)
    profit_values.append(total_day_profit)

        # Top selling products
    top_selling = Product.objects.annotate(total_sold=Sum('sale__quantity')).order_by('-total_sold')[:5]
    top_selling_labels = [p.name for p in top_selling]
    top_selling_values = [p.total_sold or 0 for p in top_selling]

    # Top profitable products
    top_profit = (
        Product.objects.annotate(
            total_sales=Coalesce(
                Sum(F('sale__quantity') * F('sale__price')),
                0,
                output_field=DecimalField()
            ),
            total_cost=Coalesce(
                Sum(F('sale__quantity') * F('purchase_price')),
                0,
                output_field=DecimalField()
            ),
        )
        .annotate(
            total_profit=ExpressionWrapper(
                F('total_sales') - F('total_cost'),
                output_field=DecimalField()
            )
        )
        .order_by('-total_profit')[:5]
    )

    top_profit_labels = [p.name for p in top_profit]
    top_profit_values = [p.total_profit for p in top_profit]

    
    context = {
        'total_sales': total_sales,
        'total_purchase': total_purchase,
        'profit': total_profit,
        'low_stock': low_stock,
        'today_sales_count': today_sales_count,
        'yesterday_sales_count': yesterday_sales_count,
        'vendors': vendors,
        'chart_labels': chart_labels,
        'sales_values': sales_values,
        'profit_values': profit_values,
        'top_selling_labels': top_selling_labels,
        'top_selling_values': top_selling_values,
       'top_profit_labels': top_profit_labels,
       'top_profit_values': top_profit_values,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'core/dashboard.html', context)

def products(request):
    products = Product.objects.select_related('subcategory', 'subcategory__category')
    categories = Category.objects.all()
    subcategories = SubCategory.objects.all()

    selected_category = request.GET.get('category')
    selected_subcategory = request.GET.get('subcategory')

    # 🔍 Apply filters
    if selected_category:
        products = products.filter(subcategory__category_id=selected_category)
    if selected_subcategory:
        products = products.filter(subcategory_id=selected_subcategory)

    # ✅ Add new product form
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('products')

    # ✅ Create a separate edit form for each product
    edit_forms = {p.id: ProductForm(instance=p) for p in products}

    context = {
        'products': products,
        'form': form,
        'edit_forms': edit_forms,
        'categories': categories,
        'subcategories': subcategories,
        'selected_category': selected_category,
        'selected_subcategory': selected_subcategory,
    }
    return render(request, 'core/products.html', context)

# views.py
from django.shortcuts import render
# from .models import Product, Category, Subcategory

def product_list_view(request):
    products = Product.objects.select_related('subcategory', 'subcategory__category')
    categories = Category.objects.all()
    subcategories = SubCategory.objects.all()

    selected_category = request.GET.get('category')
    selected_subcategory = request.GET.get('subcategory')

    # 🔍 Apply filters
    if selected_category:
        products = products.filter(subcategory__category_id=selected_category)
    if selected_subcategory:
        products = products.filter(subcategory_id=selected_subcategory)

    
    context = {
        'products': products,
        'categories': categories,
        'subcategories': subcategories,
    
    }
    return render(request, 'core/product_list.html',context)
# Add Product
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('products')
    else:
        form = ProductForm()
    return render(request, 'core/products.html', {'form': form, 'products': Product.objects.all()})

# ✏️ Edit Product
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'core/edit_product.html', {'form': form, 'product': product})


# ❌ Delete Product
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()
    return redirect('products')


# 🧾 Vendors List
# def vendors(request, edit_vendor_id=None):
#     """
#     List all vendors, add a new vendor, and edit an existing vendor in one page.
#     """
#     # Determine if we are editing
#     if edit_vendor_id:
#         vendor_instance = get_object_or_404(Vendor, id=edit_vendor_id)
#         editing = True
#     else:
#         vendor_instance = None
#         editing = False

#     # Handle form submission
#     if request.method == "POST":
#         form = VendorForm(request.POST, instance=vendor_instance)
#         if form.is_valid():
#             form.save()
#             return redirect('vendors')  # reload page after saving
#     else:
#         form = VendorForm(instance=vendor_instance)

#     # Get all vendors
#     all_vendors = Vendor.objects.all()

#     context = {
#         'form': form,
#         'vendors': all_vendors,
#         'editing': editing,
#         'edit_vendor_id': edit_vendor_id,
#     }
#     return render(request, 'core/vendors.html', context)
# def vendors(request, edit_vendor_id=None):
#     if edit_vendor_id:
#         vendor_instance = get_object_or_404(Vendor, id=edit_vendor_id)
#         editing = True
#     else:
#         vendor_instance = None
#         editing = False

#     if request.method == "POST":
#         form = VendorForm(request.POST, instance=vendor_instance)
#         if form.is_valid():
#             vendor = form.save(commit=False)
#             vendor.save()  # ✅ Save what the user entered, including balance
#             return redirect('vendors')
#     else:
#         form = VendorForm(instance=vendor_instance)

#   # ✅ Update all vendor balances, including those with opening balances only
#         all_vendors = Vendor.objects.all()
#     for vendor in all_vendors:
#         vendor.update_balance()


#     context = {
#         'form': form,
#         'vendors': all_vendors,
#         'editing': editing,
#         'edit_vendor_id': edit_vendor_id,
#     }
#     return render(request, 'core/vendors.html', context)

def vendors(request, edit_vendor_id=None):
    vendor_instance = None
    editing = False

    if edit_vendor_id:
        vendor_instance = get_object_or_404(Vendor, id=edit_vendor_id)
        editing = True

    if request.method == "POST":
        form = VendorForm(request.POST, instance=vendor_instance)
        if form.is_valid():
            vendor = form.save(commit=False)
            vendor.save()
            vendor.update_balance()
            return redirect('vendors')
    else:
        form = VendorForm(instance=vendor_instance)

    # ✅ Update all vendor balances
    all_vendors = Vendor.objects.all()
    for v in all_vendors:
        v.update_balance()

    context = {
        'form': form,
        'vendors': all_vendors,
        'editing': editing,
        'edit_vendor_id': edit_vendor_id,
    }
    return render(request, 'core/vendors.html', context)

# 💸 Payments List
def payments(request):
    payments = Payment.objects.select_related('vendor')
    form = PaymentForm()

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('payments')

    return render(request, 'core/payments.html', {'payments': payments, 'form': form})


# 📥 Purchases
def purchases(request):
    vendors = Vendor.objects.all()
    products = Product.objects.all()

    selected_vendor = request.GET.get('vendor')
    selected_product = request.GET.get('product')

    # Base queryset
    purchases = Purchase.objects.select_related('vendor', 'product').all()

    # ✅ Apply filters
    if selected_vendor:
        purchases = purchases.filter(vendor_id=selected_vendor)

    if selected_product:
        purchases = purchases.filter(product_id=selected_product)

    # Pre-calculate total_price (not really needed if already saved)
    for p in purchases:
        p.total_price = p.quantity * p.price

    # Form for adding new purchase
    form = PurchaseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        purchase = form.save()
        # Update stock
        purchase.product.stock += purchase.quantity
        purchase.product.save()
        return redirect('purchases')

    # Edit forms
    edit_forms_list = [(p, PurchaseForm(instance=p)) for p in purchases]

    context = {
        'vendors': vendors,
        'products': products,
        'purchases': purchases,
        'form': form,
        'edit_forms_list': edit_forms_list,
        'selected_vendor': selected_vendor,
        'selected_product': selected_product,
    }

    return render(request, 'core/purchases.html', context)

# Purchase Views
def add_purchase(request):
    form = PurchaseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        purchase = form.save()
        # Update stock
        product = purchase.product
        product.stock += purchase.quantity
        product.save()
        return redirect('purchases')
    return render(request, 'core/purchases.html', {'form': form, 'purchases': Purchase.objects.all()})


def edit_purchase(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    if request.method == 'POST':
        form = PurchaseForm(request.POST, instance=purchase)
        if form.is_valid():
            form.save()
            # Update stock correctly
            purchase.product.stock = sum(
                Purchase.objects.filter(product=purchase.product).values_list('quantity', flat=True)
            )
            purchase.product.save()
            return redirect('purchases')
    else:
        form = PurchaseForm(instance=purchase)
    return render(request, 'core/edit_purchase.html', {'form': form, 'purchase': purchase})



def delete_purchase(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    purchase.delete()
    return redirect('purchases')


def save(self, *args, **kwargs):
    self.total_price = self.quantity * self.price
    super().save(*args, **kwargs)

    # Create a payment record *after* saving purchase
    if self.amount_paid > 0:
        Payment.objects.create(
            vendor=self.vendor,
            purchase=self,
            amount=self.amount_paid,
            date=self.date
        )

    # ✅ Update vendor balance AFTER all saves are complete
    self.vendor.refresh_from_db()
    self.vendor.update_balance()


@property
def pending_amount(self):
    paid = sum(p.amount for p in self.payments.all())
    return self.total_price - paid
def pending_total(self):
    """Return current pending total including initial balance."""
    total_purchases = sum(p.total_price for p in self.purchases.all())
    total_payments = sum(pay.amount for pay in self.payments.all())

    # ✅ Add initial (opening) balance
    total_with_opening = self.balance + total_purchases - total_payments
    return total_with_opening


def purchase_detail(request, purchase_id):
    vendor = Vendor.objects.get(id=vendor_id)
    purchases = vendor.purchases.all()
    payments = vendor.payments.all()
    purchase = Purchase.objects.get(id=purchase_id)
    context = {
        'purchase': purchase,
        'pending_amount': purchase.pending_amount()
    }
    return render(request, 'purchase_detail.html', context)



# 💰 Sales

from django.utils import timezone

def sales(request):
    sales_qs = Sale.objects.select_related('product').all()
    fixed_sales = []
    for s in sales_qs:
        if not s.date:
            s.date = timezone.now()
            s.save()
        fixed_sales.append(s)

    form = SaleForm(request.POST or None)
    products = Product.objects.all()

    if request.method == 'POST' and form.is_valid():
        sale = form.save(commit=False)
        sale.total_price = sale.quantity * sale.price
        sale.save()
        sale.product.stock -= sale.quantity
        sale.product.save()
        return redirect('sales')

    edit_forms_list = [(s, SaleForm(instance=s)) for s in fixed_sales]

    return render(request, 'core/sales.html', {
        'form': form,
        'sales': fixed_sales,
        'products': products,
        'edit_forms_list': edit_forms_list
    })

# Vendor Views
def add_vendor(request):
    form = VendorForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('vendors')
    return render(request, 'core/vendors.html', {'form': form, 'vendors': Vendor.objects.all()})


def edit_vendor(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    form = VendorForm(request.POST or None, instance=vendor)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('vendors')
    return render(request, 'core/edit_vendor.html', {'form': form, 'vendor': vendor})


def delete_vendor(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    vendor.delete()
    return redirect('vendors')





# Sale Views
def sales(request):
    form = SaleForm(request.POST or None)
    sales = Sale.objects.select_related('product').all()
    products = Product.objects.all()

    if request.method == 'POST' and form.is_valid():
        sale = form.save(commit=False)
        sale.total_price = sale.quantity * sale.price  # calculate total
        sale.save()

        # Reduce stock
        sale.product.stock -= sale.quantity
        sale.product.save()

        return redirect('sales')

    edit_forms_list = [(s, SaleForm(instance=s)) for s in sales]

    return render(request, 'core/sales.html', {
        'form': form,
        'sales': sales,
        'products': products,
        'edit_forms_list': edit_forms_list
    })


def edit_sale(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    form = SaleForm(request.POST or None, instance=sale)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('sales')
    return render(request, 'core/edit_sale.html', {'form': form, 'sale': sale})


def delete_sale(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    sale.product.stock += sale.quantity  # restore stock
    sale.product.save()
    sale.delete()
    return redirect('sales')





# Payment Views
def add_payment(request):
    form = PaymentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('payments')
    return render(request, 'core/payments.html', {'form': form, 'payments': Payment.objects.all()})


def edit_payment(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    form = PaymentForm(request.POST or None, instance=payment)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('payments')
    return render(request, 'core/edit_payment.html', {'form': form, 'payment': payment})


def delete_payment(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    payment.delete()
    return redirect('payments')
def vendor_payments(request):
    payments = Payment.objects.select_related('vendor', 'purchase', 'recorded_by').all()
    
    # Forms
    from .forms import PaymentForm
    form = PaymentForm()
    
    # Edit forms
    edit_forms_list = [(p, PaymentForm(instance=p)) for p in payments]

    if request.method == 'POST':
        if 'add_payment' in request.POST:
            form = PaymentForm(request.POST, request.FILES)
            if form.is_valid():
                payment = form.save(commit=False)
                payment.recorded_by = request.user
                payment.save()
                payment.vendor.balance -= payment.amount
                payment.vendor.save()
                return redirect('vendor_payments')
                
    return render(request, 'core/vendor_payments.html', {
        'payments': payments,
        'form': form,
        'edit_forms_list': edit_forms_list
    })
def edit_payment(request, pk):
    payment = Payment.objects.get(pk=pk)
    form = PaymentForm(request.POST or None, request.FILES or None, instance=payment)
    if request.method == 'POST' and form.is_valid():
        old_amount = payment.amount
        payment = form.save(commit=False)
        payment.save()
        # adjust vendor balance
        payment.vendor.balance += old_amount - payment.amount
        payment.vendor.save()
        return redirect('vendor_payments')
    return render(request, 'core/edit_payment.html', {'form': form, 'payment': payment})
def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome {user.username} 👋")
            return redirect('dashboard')  # redirect to your home/dashboard
        else:
            messages.error(request, "Invalid username or password")
    return render(request, 'core/login.html')


def user_logout(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('login')
