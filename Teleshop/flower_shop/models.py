from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify

class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Телефон")
    address = models.TextField(blank=True, null=True, verbose_name="Адрес")

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

class Order(models.Model):
    STATUS_CHOICES = [
        ('accepted', 'Принят к работе'),
        ('in_progress', 'Находится в работе'),
        ('in_delivery', 'В доставке'),
        ('completed', 'Выполнен'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    products = models.ManyToManyField(Product, through='OrderItem', verbose_name="Товары")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='accepted', verbose_name="Статус заказа")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"Заказ {self.id} от {self.user.username} (Статус: {self.get_status_display()})"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name="Заказ")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    class Meta:
        verbose_name = "Элемент заказа"
        verbose_name_plural = "Элементы заказа"

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    text = models.TextField(verbose_name="Текст отзыва")
    rating = models.PositiveIntegerField(default=5, verbose_name="Рейтинг")

    def __str__(self):
        return f"Отзыв от {self.user.username} на {self.product.name}"

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

class Report(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name="Заказ")
    date = models.DateField(auto_now_add=True, verbose_name="Дата отчета")
    sales_data = models.TextField(verbose_name="Данные по продажам")
    profit = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Прибыль")
    expenses = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Расходы")

    def __str__(self):
        return f"Отчет за {self.date}"

    class Meta:
        verbose_name = "Отчет"
        verbose_name_plural = "Отчеты"
