# flower_shop/tests/test_views.py
import pytest
from django.urls import reverse
from django.test import Client
from flower_shop.models import User

@pytest.mark.django_db
def test_user_registration():
    client = Client()
    url = reverse('register')  # Замените на ваш URL для регистрации
    data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password1': 'strongpassword123',
        'password2': 'strongpassword123',
    }
    response = client.post(url, data)
    assert response.status_code == 302  # Проверяем редирект после успешной регистрации
    assert User.objects.filter(username='testuser').exists()  # Проверяем, что пользователь создан


# flower_shop/tests/test_views.py
@pytest.mark.django_db
def test_user_login():
    client = Client()
    User.objects.create_user(username='testuser', password='strongpassword123')
    url = reverse('login')  # Замените на ваш URL для авторизации
    data = {
        'username': 'testuser',
        'password': 'strongpassword123',
    }
    response = client.post(url, data)
    assert response.status_code == 302  # Проверяем редирект после успешной авторизации


# flower_shop/tests/test_views.py
from flower_shop.models import Product

@pytest.mark.django_db
def test_product_list_view():
    client = Client()
    Product.objects.create(name='Rose', price=10.0)
    url = reverse('product-list')  # Замените на ваш URL для списка товаров
    response = client.get(url)
    assert response.status_code == 200
    assert 'Rose' in str(response.content)  # Проверяем, что товар отображается


# flower_shop/tests/test_views.py
from flower_shop.models import Order, Product

@pytest.mark.django_db
def test_create_order():
    client = Client()
    user = User.objects.create_user(username='testuser', password='strongpassword123')
    product = Product.objects.create(name='Rose', price=10.0)
    client.login(username='testuser', password='strongpassword123')
    url = reverse('create-order')  # Замените на ваш URL для создания заказа
    data = {
        'products': [product.id],
        'address': '123 Main St',
    }
    response = client.post(url, data)
    assert response.status_code == 302  # Проверяем редирект после успешного создания заказа
    assert Order.objects.filter(user=user).exists()  # Проверяем, что заказ создан