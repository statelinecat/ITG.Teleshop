from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView  # Импортируем встроенные представления
from . import views
from .views import CustomLoginView

urlpatterns = [
    path('', views.index, name='index'),
    path('catalog/', views.catalog, name='catalog'),
    path('cart/', views.view_cart, name='cart_detail'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_list, name='order_list'),
    path('logout/', LogoutView.as_view(), name='user_logout'),  # Маршрут для выхода
    path('login/', CustomLoginView.as_view(), name='user_login'),  # Маршрут для входа
    path('register/', views.register, name='register'),  # Маршрут для регистрации
]