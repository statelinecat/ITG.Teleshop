from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Телефон")
    address = models.TextField(blank=True, null=True, verbose_name="Адрес")

    # Указываем уникальные related_name для groups и user_permissions
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='Группы',
        blank=True,
        related_name='flower_shop_users',  # Уникальный related_name
        related_query_name='flower_shop_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='Права доступа',
        blank=True,
        related_name='flower_shop_users',  # Уникальный related_name
        related_query_name='flower_shop_user',
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Название категории")
    slug = models.SlugField(max_length=255, unique=True, blank=True, verbose_name="URL-адрес категории")
    description = models.TextField(blank=True, null=True, verbose_name="Описание категории")
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="Изображение категории")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название товара")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Изображение товара")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="Категория")
    description = models.TextField(blank=True, null=True, verbose_name="Описание товара")
    available = models.BooleanField(default=True, verbose_name="Доступен для заказа")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Корзина пользователя {self.user.username}"

    def get_total_price(self):
        """
        Возвращает общую стоимость товаров в корзине.
        """
        return sum(item.product.price * item.quantity for item in self.items.all())

    def get_total_quantity(self):
        """
        Возвращает общее количество товаров в корзине.
        """
        return sum(item.quantity for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    class Meta:
        verbose_name = "Элемент корзины"
        verbose_name_plural = "Элементы корзины"

class Order(models.Model):
    STATUS_CHOICES = [
        ('accepted', 'Принят к работе'),
        ('in_progress', 'Находится в работе'),
        ('in_delivery', 'В доставке'),
        ('completed', 'Выполнен'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='accepted', verbose_name="Статус заказа")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    # Поля для данных заказа
    name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Имя")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Телефон")
    address = models.TextField(blank=True, null=True, verbose_name="Адрес доставки")
    delivery_time = models.DateTimeField(blank=True, null=True, verbose_name="Время доставки")
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий")

    def __str__(self):
        return f"Заказ {self.id} от {self.user.username} (Статус: {self.get_status_display()})"

    def get_total_price(self):
        """
        Возвращает общую стоимость заказа.
        """
        return sum(item.product.price * item.quantity for item in self.items.all())

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Заказ")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    class Meta:
        verbose_name = "Элемент заказа"
        verbose_name_plural = "Элементы заказа"

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    text = models.TextField(verbose_name="Текст отзыва")
    rating = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Рейтинг"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"Отзыв от {self.user.username} на {self.product.name}"

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

def default_period_start():
    return timezone.now().date()

def default_period_end():
    return timezone.now().date()

class Report(models.Model):
    date = models.DateField(auto_now_add=True, verbose_name="Дата отчета")
    total_orders = models.PositiveIntegerField(default=0, verbose_name="Общее количество заказов")
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Общая выручка")
    period_start = models.DateField(default=default_period_start, verbose_name="Начало периода")  # Используем функцию
    period_end = models.DateField(default=default_period_end, verbose_name="Конец периода")  # Используем функцию

    def __str__(self):
        return f"Отчет за {self.period_start} - {self.period_end}"

    def profit(self):
        return self.total_revenue * 0.2  # Пример: 20% прибыли

    def expenses(self):
        return self.total_revenue * 0.1  # Пример: 10% расходов

    class Meta:
        verbose_name = "Отчет"
        verbose_name_plural = "Отчеты"


# Сигнал для автоматического создания корзины при создании пользователя
@receiver(post_save, sender=User)
def create_user_cart(sender, instance, created, **kwargs):
    if created:
        Cart.objects.create(user=instance)