from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),  # Админка Django
    path('', include('flower_shop.urls')),  # Подключаем маршруты из приложения flower_shop
]