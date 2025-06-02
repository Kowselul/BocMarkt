from django.urls import path
from . import views
from django.conf.urls import handler404

urlpatterns = [
    # Core Pages
    # Handles main application pages and authentication
    path('', views.homepage, name="homepage"),
    path('register/', views.register, name="register"),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name="logout"),
    path('dashboard/', views.dashboard, name="dashboard"),

    # User Profile Management
    # Handles user profile settings and viewing
    path('account-settings/', views.account_settings, name='account_settings'),
    path('profile/', views.user_profile, name='user_profile'),
    path('user/<int:user_id>/', views.view_user_profile, name='user_profile'),

    # Product Management
    # Handles product creation, editing, and deletion
    path('add-product/', views.add_product, name="add_product"),
    path('edit-product/<int:pk>/', views.edit_product, name='edit_product'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('delete-product-image/<int:image_id>/', views.delete_product_image, name='delete_product_image'),
    path('cleanup-sold-items/', views.cleanup_sold_items, name='cleanup_sold_items'),

    # Marketplace
    # Handles product browsing and viewing
    path('marketplace/', views.marketplace, name='marketplace'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),

    # Favorites System
    # Manages user's favorite products
    path('marketplace/favorites/', views.favorites, name='favorites'),
    path('marketplace/toggle-favorite/<int:product_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('favorites/count/', views.get_favorites_count, name='favorites_count'),
    path('toggle-favorite/<int:product_id>/', views.toggle_favorite, name='toggle_favorite'),

    # Shopping Cart
    # Handles shopping cart operations
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/count/', views.get_cart_count, name='cart_count'),
    path('toggle-cart/<int:product_id>/', views.toggle_cart, name='toggle_cart'),

    # Order Processing
    # Manages order creation and processing
    path('checkout/', views.checkout, name='checkout'),
    path('submit-order/', views.submit_order, name='submit_order'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('my-orders/', views.my_orders, name='my_orders'),

    # Wallet System
    # Handles financial transactions and wallet management
    path('wallet/', views.wallet_view, name='wallet'),
    path('withdraw-funds/', views.withdraw_funds, name='withdraw_funds'),
    path('add-funds/', views.add_funds, name='add_funds'),
]

# Custom error handling
handler404 = 'bocmarkt1.views.custom_404'