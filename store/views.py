from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
import datetime
from .models import *
from .forms import CreateUserForm
from .utils import cookieCart, cartData, guestOrder
from django.contrib.auth.forms import UserCreationForm

def registerPage(request):
    form = CreateUserForm()
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            redirect('store/login.html')

    context = {'form':form}
    return render(request,'store/register.html', context)

def loginPage(request):
    context = {}
    return render(request, 'store/login.html', context )

def store(request):
    data = cartData(request)
    cartItems = data['cartItems']

    if(request.GET.get('filter') == 'price_inc'):
        products = Product.objects.all().order_by('price')
    elif(request.GET.get('filter') == 'price_dec'):
        products = Product.objects.all().order_by('-price')
    elif(request.GET.get('filter') == 'nameA_Z'):
        products = Product.objects.all().order_by('name')
    else:
        products = Product.objects.all()

    context = {'products': products, 'cartItems': cartItems}
    return render(request, 'store/store.html', context)


def cart(request):
    data = cartData(request)
    items = data['items']
    order = data['order']
    cartItems = data['cartItems']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/cart.html', context)

def checkout(request):
    data = cartData(request)
    items = data['items']
    order = data['order']
    cartItems = data['cartItems']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/checkout.html', context)


def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    print('productId: ', productId)
    print('action: ', action)

    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(
        customer=customer, complete=False)

    orderItem, created = OrderItem.objects.get_or_create(
        order=order, product=product)
    if action == 'add':
        orderItem.quantity += 1
    elif action == 'remove':
        orderItem.quantity -= 1

    orderItem.save()
    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was added', safe=False)


# @csrf_exempt
def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    print("transaction_id,", transaction_id)
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(
            customer=customer, complete=False)

        if order.shipping == True:
            ShippingAddress.objects.create(
                customer=customer,
                order=order,
                address=data['shipping']['address'],
                city=data['shipping']['city'],
                state=data['shipping']['state'],
                zipcode=data['shipping']['zipcode'],
                contact=data['shipping']['contact']
            )

    else:
        customer, order = guestOrder(request, data)

    total = float(data['form']['total'])
    order.transaction_id = transaction_id

    if total == float(order.get_cart_total):
        order.complete = True
    order.save()

    return JsonResponse('Payment Submitted', safe=False)
