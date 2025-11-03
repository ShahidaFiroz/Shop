from django import forms
from .models import Product, Vendor, Purchase, Sale, Payment , Category, SubCategory

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubCategory
        fields = ['category', 'name']

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields =[ 'subcategory', 'name', 'stock', 'purchase_price', 'sale_price','image']

def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subcategory'].queryset = SubCategory.objects.none()
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = SubCategory.objects.filter(category_id=category_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['subcategory'].queryset = self.instance.category.subCategory_set




class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['name', 'phone', 'opening_balance']
class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['vendor', 'product', 'quantity', 'price', 'amount_paid', 'date']

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['product', 'quantity', 'price']



class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['vendor', 'amount', 'date']
