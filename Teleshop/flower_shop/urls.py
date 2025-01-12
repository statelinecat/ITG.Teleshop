from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.contrib.auth.views import (
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from . import views
from .views import (
    CustomLoginView,
    order_report,
    export_order_report,
    export_order_report_excel,
    generate_link_code,  # Импортируем generate_link_code
)

urlpatterns = [
    # Основные маршруты
    path('', views.index, name='index'),
    path('catalog/', views.catalog, name='catalog'),
    path('cart/', views.view_cart, name='cart_detail'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_cart_item'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_list, name='order_list'),
    path('logout/', LogoutView.as_view(next_page='index'), name='user_logout'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', views.register, name='register'),
    path('category/<slug:category_slug>/', views.product_list_by_category, name='product_list_by_category'),
    path('orders/reorder/<int:order_id>/', views.reorder, name='reorder'),
    path('product/<int:product_id>/reviews/', views.product_reviews, name='product_reviews'),
    path('product/<int:product_id>/add_review/', views.add_review, name='add_review'),

    # Маршруты для восстановления пароля
    path('password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Маршруты для администратора
    path('order/change_status/<int:order_id>/', views.change_order_status, name='change_order_status'),
    path('order_report/', order_report, name='order_report'),
    path('export_order_report/', export_order_report, name='export_order_report'),
    path('export_order_report_excel/', export_order_report_excel, name='export_order_report_excel'),

    # Маршрут для генерации кода привязки Telegram
    path('generate-link-code/', generate_link_code, name='generate_link_code'),
]

# Добавляем маршруты для медиа-файлов в режиме DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)