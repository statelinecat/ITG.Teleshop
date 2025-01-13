from django.contrib import admin
from .models import User, Category, Product, Order, OrderItem, Review, Report

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone', 'address')
    search_fields = ('username', 'email', 'phone')
    list_filter = ('is_staff', 'is_superuser')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}  # Автоматическое создание slug из name

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'available')
    list_filter = ('category', 'available')
    search_fields = ('name', 'category__name')
    list_editable = ('price', 'available')  # Позволяет редактировать прямо в списке

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0  # Не показывать дополнительные пустые строки
    readonly_fields = ('get_total_price',)  # Добавляем вычисляемое поле

    def get_total_price(self, obj):
        return obj.product.price * obj.quantity
    get_total_price.short_description = 'Общая стоимость'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'get_status_display', 'created_at', 'get_total_price_display')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'id')
    date_hierarchy = 'created_at'  # Иерархия по датам
    readonly_fields = ('created_at',)  # Поле только для чтения
    inlines = [OrderItemInline]  # Добавляем вложенные элементы заказа

    def get_total_price_display(self, obj):
        return obj.get_total_price()
    get_total_price_display.short_description = 'Общая сумма заказа'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'get_total_price')
    search_fields = ('order__id', 'product__name')

    def get_total_price(self, obj):
        return obj.product.price * obj.quantity
    get_total_price.short_description = 'Общая стоимость'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'product__name')
    readonly_fields = ('created_at',)

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_orders', 'total_revenue', 'profit', 'expenses', 'period_start', 'period_end')
    list_filter = ('date',)
    search_fields = ('period_start', 'period_end')
    date_hierarchy = 'date'  # Иерархия по датам

    def profit(self, obj):
        """
        Возвращает прибыль (20% от выручки).
        """
        return obj.total_revenue * 0.2

    def expenses(self, obj):
        """
        Возвращает расходы (10% от выручки).
        """
        return obj.total_revenue * 0.1

    profit.short_description = 'Прибыль'
    expenses.short_description = 'Расходы'