from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from .forms import CustomLoginForm, CustomRegistrationForm
from .models import Category, Product, Cart, CartItem, Order


def index(request):
    categories = Category.objects.all()
    popular_products = Product.objects.filter(available=True)[:5]  # Первые 5 доступных товаров
    return render(request, 'flower_shop/index.html', {
        'categories': categories,
        'popular_products': popular_products,
    })

def catalog(request):
    products = Product.objects.filter(available=True)
    return render(request, 'flower_shop/catalog.html', {'products': products})

@login_required
def view_cart(request):
    cart = get_object_or_404(Cart, user=request.user)
    return render(request, 'flower_shop/cart.html', {'cart': cart})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('catalog')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    return redirect('cart_detail')

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    if request.method == 'POST':
        # Логика оформления заказа
        cart.items.all().delete()
        return redirect('order_history')
    return render(request, 'flower_shop/checkout.html', {'cart': cart})


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'flower_shop/order_list.html', {'orders': orders})

def register(request):
    if request.method == 'POST':
        form = CustomRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Автоматически входим после регистрации
            return redirect('index')
    else:
        form = CustomRegistrationForm()
    return render(request, 'flower_shop/register.html', {'form': form})

class CustomLoginView(LoginView):
    form_class = CustomLoginForm
    template_name = 'flower_shop/login.html'