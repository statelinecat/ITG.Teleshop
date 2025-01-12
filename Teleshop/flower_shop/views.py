import csv
import logging
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from datetime import datetime, timedelta

from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.views.decorators.http import require_http_methods
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from django.http import HttpResponse

from .models import User, Review, Report

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
    Оформление заказа. Подставляет значения из последнего заказа пользователя, если он существует.
    """
    cart = get_object_or_404(Cart, user=request.user)

    # Получаем последний заказ пользователя
    last_order = Order.objects.filter(user=request.user).order_by('-created_at').first()

    # Значения по умолчанию
    default_name = request.user.username  # Имя пользователя
    default_phone = "+79991237567"  # Номер телефона
    default_address = "Самовывоз"  # Адрес доставки
    default_delivery_time = (timezone.now() + timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)  # Завтра в 12:00
    default_comment = "Я люблю Лепесток"  # Комментарий

    # Если есть последний заказ, используем его данные
    if last_order:
        default_name = last_order.name if last_order.name else default_name
        default_phone = last_order.phone if last_order.phone else default_phone
        default_address = last_order.address if last_order.address else default_address
        default_delivery_time = last_order.delivery_time.strftime('%Y-%m-%dT%H:%M') if last_order.delivery_time else default_delivery_time.strftime('%Y-%m-%dT%H:%M')
        default_comment = last_order.comment if last_order.comment else default_comment

    if request.method == 'POST':
        # Создаем заказ
        order = Order.objects.create(
            user=request.user,
            status='accepted',
            name=request.POST.get('name'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            delivery_time=request.POST.get('delivery_time'),
            comment=request.POST.get('comment')
        )
        for item in cart.items.all():
            OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity)
        # Очищаем корзину
        cart.items.all().delete()
        messages.success(request, 'Заказ успешно оформлен!')
        return redirect('order_list')  # Перенаправляем на список заказов

    # Передаем корзину и значения по умолчанию в контекст шаблона
    return render(request, 'flower_shop/checkout.html', {
        'cart': cart,
        'default_name': default_name,
        'default_phone': default_phone,
        'default_address': default_address,
        'default_delivery_time': default_delivery_time,
        'default_comment': default_comment,
    })


@login_required
def order_list(request):
    """
    Список заказов пользователя (или всех заказов для администратора) с фильтрацией по статусу и датам.
    По умолчанию отображаются заказы за текущий день (с учетом локального времени).
    """
    # Получаем выбранные статусы и даты из GET-запроса
    selected_statuses = request.GET.getlist('status')  # Множественный выбор статусов
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Устанавливаем значения по умолчанию для дат (текущий день)
    today_local = timezone.localtime(timezone.now()).date()  # Текущая дата в локальном времени
    if not start_date:
        start_date = today_local
    if not end_date:
        end_date = today_local

    # Преобразуем start_date и end_date в объекты date
    if isinstance(start_date, str):
        start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()

    # Преобразуем даты в UTC для фильтрации
    start_datetime_utc = timezone.make_aware(timezone.datetime.combine(start_date, timezone.datetime.min.time()))
    end_datetime_utc = timezone.make_aware(timezone.datetime.combine(end_date + timedelta(days=1), timezone.datetime.min.time()))

    # Базовый запрос для заказов
    if request.user.is_staff:
        orders = Order.objects.all().prefetch_related('items__product')  # Все заказы для администратора
    else:
        orders = Order.objects.filter(user=request.user).prefetch_related('items__product')  # Только заказы пользователя

    # Фильтрация по статусам, если статусы выбраны
    if selected_statuses:
        orders = orders.filter(status__in=selected_statuses)

    # Фильтрация по датам
    orders = orders.filter(created_at__gte=start_datetime_utc, created_at__lt=end_datetime_utc)

    return render(request, 'flower_shop/order_list.html', {
        'orders': orders,
        'selected_statuses': selected_statuses,  # Передаем выбранные статусы в шаблон
        'status_choices': Order.STATUS_CHOICES,  # Передаем все возможные статусы
        'start_date': start_date.strftime('%Y-%m-%d'),  # Передаем начальную дату в шаблон
        'end_date': end_date.strftime('%Y-%m-%d'),  # Передаем конечную дату в шаблон
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
    """
    Изменение статуса заказа с сохранением текущих параметров фильтрации.
    """
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')  # Новый статус заказа
        if new_status in dict(Order.STATUS_CHOICES).keys():  # Проверяем, что статус допустим
            order.status = new_status
            order.save()

        # Получаем параметры фильтрации из POST-запроса
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        filter_statuses = request.POST.getlist('filter_status')  # Список статусов фильтрации

        # Формируем параметры для URL
        filter_params = {}
        if start_date:
            filter_params['start_date'] = start_date
        if end_date:
            filter_params['end_date'] = end_date
        if filter_statuses:
            filter_params['status'] = filter_statuses  # Используем filter_statuses для фильтрации

        # Формируем URL с текущими параметрами фильтрации
        url = reverse('order_list')  # Базовый URL для списка заказов
        if filter_params:
            url += '?' + urlencode(filter_params, doseq=True)  # Добавляем параметры фильтрации

        return redirect(url)  # Перенаправляем с сохранением фильтров

    return redirect('order_list')  # Если метод не POST, просто перенаправляем на список заказов

@user_passes_test(lambda u: u.is_staff)  # Только для администраторов
def order_report(request):
    """
    Формирование отчёта по заказам за определённый период с детализацией по дням.
    По умолчанию отчёт за текущий день.
    """
    # Получаем даты из GET-запроса
    start_date = request.GET.get('start_date', timezone.now().date())
    end_date = request.GET.get('end_date', timezone.now().date())

    # Преобразуем строки в объекты date
    if isinstance(start_date, str):
        start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()

    # Фильтруем заказы за указанный период
    orders = Order.objects.filter(created_at__date__range=(start_date, end_date))

    # Группируем заказы по дням
    daily_stats = (
        orders
        .values('created_at__date')  # Группируем по дате
        .annotate(
            total_orders=Count('id'),  # Количество заказов за день
            total_revenue=Sum('items__product__price')  # Выручка за день
        )
        .order_by('created_at__date')  # Сортируем по дате
    )

    # Считаем общее количество заказов и выручку за весь период
    total_orders = orders.count()
    total_revenue = orders.aggregate(total_revenue=Sum('items__product__price'))['total_revenue'] or 0

    # Сохраняем отчёт в базу данных (опционально)
    report = Report.objects.create(
        date=timezone.now().date(),
        total_orders=total_orders,
        total_revenue=total_revenue,
        period_start=start_date,
        period_end=end_date
    )

    # Передаем данные в шаблон
    return render(request, 'flower_shop/order_report.html', {
        'start_date': start_date,
        'end_date': end_date,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'daily_stats': daily_stats,  # Статистика по дням
    })

logger = logging.getLogger(__name__)

@user_passes_test(lambda u: u.is_staff)
def export_order_report(request):
    start_date = request.GET.get('start_date', timezone.now().date())
    end_date = request.GET.get('end_date', timezone.now().date())
    orders = Order.objects.filter(created_at__date__range=(start_date, end_date))
    total_orders = orders.count()
    total_revenue = sum(order.get_total_price() for order in orders)

    logger.debug(f"Exporting report for {start_date} to {end_date}: {total_orders} orders, {total_revenue} revenue")

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="order_report_{start_date}_{end_date}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Период', 'Количество заказов', 'Выручка'])
    writer.writerow([f'{start_date} - {end_date}', total_orders, total_revenue])

    return response


@user_passes_test(lambda u: u.is_staff)
def export_order_report_excel(request):
    start_date = request.GET.get('start_date', timezone.now().date())
    end_date = request.GET.get('end_date', timezone.now().date())
    orders = Order.objects.filter(created_at__date__range=(start_date, end_date))
    total_orders = orders.count()
    total_revenue = sum(order.get_total_price() for order in orders)

    # Создаем новый Excel-файл
    wb = Workbook()
    ws = wb.active
    ws.title = "Отчёт по заказам"

    # Заголовок отчёта
    ws['A1'] = "Отчёт по заказам"
    ws['A1'].font = Font(size=14, bold=True)
    ws.merge_cells('A1:C1')

    # Период отчёта
    ws['A2'] = f"Период: {start_date} - {end_date}"
    ws['A2'].font = Font(bold=True)
    ws.merge_cells('A2:C2')

    # Общее количество заказов и выручка
    ws['A3'] = f"Общее количество заказов: {total_orders}"
    ws['A4'] = f"Общая выручка: {total_revenue} руб."
    ws['A3'].font = Font(bold=True)
    ws['A4'].font = Font(bold=True)

    # Заголовки таблицы
    ws['A6'] = "Дата"
    ws['B6'] = "Количество заказов"
    ws['C6'] = "Выручка"
    for cell in ws['6:6']:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')

    # Данные по дням
    daily_stats = (
        orders
        .values('created_at__date')
        .annotate(
            total_orders=Count('id'),
            total_revenue=Sum('items__product__price')
        )
        .order_by('created_at__date')
    )

    row = 7
    for stat in daily_stats:
        ws[f'A{row}'] = stat['created_at__date'].strftime('%d.%m.%Y')
        ws[f'B{row}'] = stat['total_orders']
        ws[f'C{row}'] = stat['total_revenue']
        row += 1

    # Настройка ширины столбцов
    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 20

    # Создаем HTTP-ответ с Excel-файлом
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="order_report_{start_date}_{end_date}.xlsx"'
    wb.save(response)

    return response

