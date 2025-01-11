from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render, get_object_or_404, redirect
from datetime import datetime, timedelta
from django.views.decorators.http import require_http_methods
from .models import User, Review

from .forms import CustomLoginForm, CustomRegistrationForm
from .models import Category, Product, Cart, CartItem, Order, OrderItem

def index(request):
    categories = Category.objects.all()
    return render(request, 'flower_shop/index.html', {
        'categories': categories,
    })

def catalog(request):
    """
    Страница каталога товаров.
    """
    products = Product.objects.filter(available=True)
    return render(request, 'flower_shop/catalog.html', {'products': products})

@login_required
def view_cart(request):
    """
    Страница корзины пользователя.
    """
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'flower_shop/cart.html', {'cart': cart})


@login_required
def add_to_cart(request, product_id):
    """
    Добавление товара в корзину.
    """
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, f'Товар "{product.name}" добавлен в корзину.')
    return redirect(request.META.get('HTTP_REFERER', 'index'))

@login_required
def remove_from_cart(request, item_id):
    """
    Удаление товара из корзины.
    """
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    return redirect('cart_detail')


@login_required
def checkout(request):
    """
    Оформление заказа.
    """
    cart = get_object_or_404(Cart, user=request.user)

    # Значения по умолчанию
    default_name = request.user.username  # Имя пользователя
    default_phone = "+79991237567"  # Номер телефона
    default_address = "Самовывоз"  # Адрес доставки
    default_delivery_time = (datetime.now() + timedelta(days=1)).replace(hour=12, minute=0, second=0,
                                                                         microsecond=0)  # Завтра в 12:00
    default_comment = "Я люблю Лепесток"  # Комментарий

    if request.method == 'POST':
        # Создаем заказ
        order = Order.objects.create(user=request.user, status='accepted')
        for item in cart.items.all():
            OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity)
        # Очищаем корзину
        cart.items.all().delete()
        return redirect('order_list')  # Перенаправляем на список заказов

    # Передаем корзину и значения по умолчанию в контекст шаблона
    return render(request, 'flower_shop/checkout.html', {
        'cart': cart,
        'default_name': default_name,
        'default_phone': default_phone,
        'default_address': default_address,
        'default_delivery_time': default_delivery_time.strftime('%Y-%m-%dT%H:%M'),
        # Форматируем для input[type="datetime-local"]
        'default_comment': default_comment,
    })
@login_required
def order_list(request):
    """
    Список заказов пользователя (или всех заказов для администратора) с фильтрацией по статусу.
    """
    # Получаем выбранный статус из GET-запроса
    selected_status = request.GET.get('status')

    # Базовый запрос для заказов
    if request.user.is_staff:
        orders = Order.objects.all().prefetch_related('items__product')  # Все заказы для администратора
    else:
        orders = Order.objects.filter(user=request.user).prefetch_related('items__product')  # Только заказы пользователя

    # Фильтрация по статусу, если статус выбран
    if selected_status:
        orders = orders.filter(status=selected_status)

    return render(request, 'flower_shop/order_list.html', {
        'orders': orders,
        'selected_status': selected_status,  # Передаем выбранный статус в шаблон
        'status_choices': Order.STATUS_CHOICES,  # Передаем все возможные статусы
    })

def register(request):
    """
    Регистрация нового пользователя.
    """
    if request.method == 'POST':
        form = CustomRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Указываем бэкенд при вызове login()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('index')  # Перенаправляем на главную страницу
    else:
        form = CustomRegistrationForm()
    return render(request, 'flower_shop/register.html', {'form': form})

class CustomLoginView(LoginView):
    form_class = CustomLoginForm
    template_name = 'flower_shop/login.html'

def product_list_by_category(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    products_list = Product.objects.filter(category=category).order_by('name')  # Добавлена сортировка

    # Пагинация: 6 товаров на странице
    paginator = Paginator(products_list, 6)
    page = request.GET.get('page')  # Получаем номер страницы из запроса

    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        # Если page не является целым числом, показываем первую страницу
        products = paginator.page(1)
    except EmptyPage:
        # Если page выходит за пределы диапазона, показываем последнюю страницу
        products = paginator.page(paginator.num_pages)

    return render(request, 'flower_shop/product_list.html', {
        'category': category,
        'products': products,
    })

@login_required
def update_cart_item(request, item_id):
    """
    Обновление количества товара в корзине.
    """
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()
    return redirect('cart_detail')

@login_required
def reorder(request, order_id):
    """
    Повторение заказа: добавление товаров из заказа в корзину.
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    cart, created = Cart.objects.get_or_create(user=request.user)

    # Добавляем товары из заказа в корзину
    for item in order.items.all():
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=item.product)
        if not created:
            cart_item.quantity += item.quantity
        else:
            cart_item.quantity = item.quantity
        cart_item.save()

    return redirect('cart_detail')

def product_reviews(request, product_id):
    """
    Страница с отзывами о товаре.
    """
    product = get_object_or_404(Product, id=product_id)
    reviews = Review.objects.filter(product=product)
    return render(request, 'flower_shop/product_reviews.html', {
        'product': product,
        'reviews': reviews,
    })

@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        text = request.POST.get('text')
        rating = request.POST.get('rating')
        Review.objects.create(user=request.user, product=product, text=text, rating=rating)
    return redirect('product_reviews', product_id=product.id)

@user_passes_test(lambda u: u.is_staff)  # Только для администраторов
def change_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES).keys():  # Проверяем, что статус допустим
            order.status = new_status
            order.save()
    return redirect('order_list')  # Перенаправляем на страницу списка заказов