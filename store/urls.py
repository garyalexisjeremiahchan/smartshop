from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('categories/', views.category_list, name='category_list'),
    path('category/<slug:slug>/', views.category_list, name='category_detail'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/<str:order_number>/', views.order_detail, name='order_detail'),
    path('orders/', views.order_history, name='order_history'),
    # API endpoints for search autocomplete
    path('api/autocomplete/', views.autocomplete_search, name='autocomplete_search'),
    path('api/trending/', views.trending_searches, name='trending_searches'),
]
