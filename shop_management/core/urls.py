from django.urls import path
from . import views
from django.shortcuts import redirect
from .views import product_list_view
urlpatterns = [
    path('', lambda request: redirect('login'), name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Products
    path('products/', views.products, name='products'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/edit/<int:pk>/', views.edit_product, name='edit_product'),
    path('products/delete/<int:pk>/', views.delete_product, name='delete_product'),
    path('products/cards/', product_list_view, name='product_list'),
    # Vendors
    path('vendors/', views.vendors, name='vendors'),
    path('vendors/edit/<int:edit_vendor_id>/', views.vendors, name='vendors_edit'),
    path('vendors/delete/<int:pk>/', views.delete_vendor, name='vendors_delete'),

    # Purchases
    path('purchases/', views.purchases, name='purchases'),
    path('purchases/add/', views.add_purchase, name='add_purchase'),
    path('purchases/edit/<int:pk>/', views.edit_purchase, name='edit_purchase'),
    path('purchases/delete/<int:pk>/', views.delete_purchase, name='delete_purchase'),

    # Sales
    path('sales/', views.sales, name='sales'),
    path('sales/add/', views.sales, name='add_sale'),
    path('sales/edit/<int:pk>/', views.edit_sale, name='edit_sale'),
    path('sales/delete/<int:pk>/', views.delete_sale, name='delete_sale'),

    # Payments
    path('payments/', views.payments, name='payments'),
    path('payments/add/', views.add_payment, name='add_payment'),
    path('payments/edit/<int:pk>/', views.edit_payment, name='edit_payment'),
    path('payments/delete/<int:pk>/', views.delete_payment, name='delete_payment'),
]
