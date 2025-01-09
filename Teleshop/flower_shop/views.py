from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Category, Product, Order, OrderItem

def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    return render(request, 'flower_shop/product_list.html', {
        'category': category,
        'categories': categories,
        'products': products,
    })

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    order, created = Order.objects.get_or_create(user=request.user, status='accepted')
    order_item, created = OrderItem.objects.get_or_create(order=order, product=product)
    if not created:
        order_item.quantity += 1
        order_item.save()
    return redirect('product_list')

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).exclude(status='accepted')
    return render(request, 'flower_shop/order_history.html', {'orders': orders})