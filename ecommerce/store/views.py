from django.shortcuts import render,redirect # type: ignore
from django.http import JsonResponse # type: ignore
from django.contrib.auth.models import User # type: ignore
from django.contrib import messages # type: ignore
from django.contrib.auth import authenticate, login # type: ignore
from django.contrib.auth import logout # type: ignore
from django.contrib import messages # type: ignore
import json
import datetime
from .models import * 
from .utils import cookieCart, cartData, guestOrder
from django.shortcuts import get_object_or_404, redirect # type: ignore
from django.shortcuts import render, redirect # type: ignore
from .models import Coupon
from django.utils import timezone # type: ignore

import logging

def store(request):
	data = cartData(request)
	products = Product.objects.all()
	cartItems = data['cartItems']
	order = data['order']
	items = data['items']
	  
	#---------------
	name_filter = request.GET.get('name', '')
	min_price = request.GET.get('min_price', '')
	max_price = request.GET.get('max_price', '')

	# Apply name filter
	if name_filter:
		products = products.filter(name__icontains=name_filter)
	if min_price:
		products = products.filter(price__gte=min_price)
	# Apply price range filter
	if max_price:
		products = products.filter(price__lte=max_price)

	#---------------
	user = request.user if request.user.is_authenticated else "Guest"
	# return render(request, 'store/store.html', {})

	#---------------
	context = {'products':products, 'cartItems':cartItems,'user': user}
	return render(request, 'store/store.html', context)


def cart(request):
	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/cart.html', context)

def checkout(request):
    # Retrieve cart data (assuming cartData is a custom function for handling the cart)
    data = cartData(request)
    
    # Cart items and order details
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    # Calculate the total price of the items in the cart
    total_price = sum(item.product.price * item.quantity for item in items)  # Example calculation, adjust as per your data model
    final_price = total_price

    # Apply coupon if it's posted
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            if coupon.is_valid():
                # Calculate the discount
                discount = coupon.discount_percent / 100 * total_price
                final_price = total_price - discount
                messages.success(request, f'Coupon applied! You saved {coupon.discount_percent}%')
            else:
                messages.error(request, 'Coupon is not valid or has expired.')
        except Coupon.DoesNotExist:
            messages.error(request, 'Invalid coupon code.')

    # Pass the values to the template context
    context = {
        'items': items, 
        'order': order, 
        'cartItems': cartItems,
        'total_price': total_price, 
        'final_price': final_price
    }
    return render(request, 'store/checkout.html', context)

def updateItem(request):
	data = json.loads(request.body)
	productId = data['productId']
	action = data['action']
	print('Action:', action)
	print('Product:', productId)

	customer = request.user.customer
	product = Product.objects.get(id=productId)
	order, created = Order.objects.get_or_create(customer=customer, complete=False)

	orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

	if action == 'add':
		orderItem.quantity = (orderItem.quantity + 1)
	elif action == 'remove':
		orderItem.quantity = (orderItem.quantity - 1)

	orderItem.save()

	if orderItem.quantity <= 0:
		orderItem.delete()

	return JsonResponse('Item was added', safe=False)

def processorder(request):
	transaction_id = datetime.datetime.now().timestamp()
	data = json.loads(request.body)

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
	else:
		customer, order = guestOrder(request, data)

	total = float(data['form']['total'])
	order.transaction_id = transaction_id

	if total == order.get_cart_total:
		order.complete = True
	order.save()

	if order.shipping == True:
		ShippingAddress.objects.create(
		customer=customer,
		order=order,
		address=data['shipping']['address'],
		city=data['shipping']['city'],
		state=data['shipping']['state'],
		zipcode=data['shipping']['zipcode'],
		)

	return JsonResponse('Payment submitted..', safe=False)


#Login ,register,logout



def register(request):
	if request.method == 'POST':
		username = request.POST['username']
		firstname = request.POST['firstname']
		lastname = request.POST['lastname']
		email = request.POST['email']
		password = request.POST['password']
		confirm_password = request.POST['confirm_password']

		if password != confirm_password:
			messages.error(request, "Passwords do not match!")
			return redirect('register')  # Use the URL name

		if User.objects.filter(email=email).exists():
			messages.error(request, "Email already exists!")
			return redirect('register')  # Redirect back to register

		user = User.objects.create_user(username=username, email=email, password=password, first_name=firstname, last_name=lastname)
		Customer.objects.create(
			user = user , 
			name = username,
			email=email
		)

		user.save()
		messages.success(request, "Registration successful!")
		return redirect('login')  # Redirect to the login page

	return render(request, 'store/register.html')



def login_view(request):
	if request.method == 'POST':
		# email = request.POST['email']
		# password = request.POST['password']
		email = request.POST.get('email')
		password = request.POST.get('password')


		try:
			# Retrieve the user by email
			username = User.objects.get(email=email).username

			user = authenticate(request, username=username, password=password)
			if user is not None:
				login(request, user) 
				messages.success(request, "Login successful!")
				return redirect('store')  # Redirect to home or dashboard
			else:
				messages.error(request, "Invalid credentials!")
				return redirect('login')
		
		except User.DoesNotExist:
			messages.error(request, "No account found with this email!")
			return redirect('login')

	return render(request, 'store/login.html')

def logout_view(request):
	logout(request)
	messages.success(request, "Logged out successfully!")
	return redirect('store')  # Redirect to the home page


#Favorite

def updateFavorite(request):
	if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
		if request.user.is_authenticated:
			try:
				data = json.loads(request.body)
				productId = data['productId']

				customer = Customer.objects.get(user=request.user)
				product = Product.objects.get(id=productId)
				logger = logging.getLogger("Testing")
				logger.debug(f"the values are {product} | {customer}")
				
				if Favourite.objects.filter(customer=customer, product=product).exists():
					return JsonResponse({'status': 'Item already added to favorites'}, status=200)

				Favourite.objects.create(customer=customer, product=product)
				return JsonResponse({'status': 'Item successfully added to favorites'}, status=200)

			except Product.DoesNotExist:
				return JsonResponse({'status': 'Product does not exist'}, status=404)
			except Exception as e:
				return JsonResponse({'status': f'Error: {str(e)}'}, status=500)

		else:
			return JsonResponse({'status': 'Login to add favorite items'}, status=401)

	return JsonResponse({'status': 'Invalid request'}, status=400)

def favData(request):
	if request.user.is_authenticated:
		customer = Customer.objects.get(user=request.user)
		favorites = Favourite.objects.filter(customer=customer)
		return {'favorites': favorites}
	else:
		return {'favorites': []}

def favPage(request):
		if request.user.is_authenticated:
			data = favData(request)
			favorites = data['favorites']
			return render(request, 'store/fav.html', {'items': favorites})
		else:
			return redirect('login')


def removeFavorite(request, id):
	if request.user.is_authenticated:
		favorite_item = get_object_or_404(Favourite, id=id, customer__user=request.user)
		favorite_item.delete()
		return redirect('favviewpage')
	else:
		return redirect('login')

#Dashboard	

def profile(request,username):
	if request.user.is_authenticated:
		customer = User.objects.get(username=username)
		return render(request,'store/profile.html',{'customer':customer})
	else:
		messages.error(request,"No Data Available")






