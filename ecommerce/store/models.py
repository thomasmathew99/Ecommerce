from django.db import models # type: ignore
from django.contrib.auth.models import User # type: ignore
from django.db import models # type: ignore
import random
import string
from django.utils import timezone # type: ignore

# Create your models here.

class Customer(models.Model):
	user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)  #one to one relationship between user and customer 1 user = 1  customer
	name = models.CharField(max_length=200, null=True)	
	email = models.CharField(max_length=200)

	def __str__(self):
		return self.name #returning string for display properly in admin


class Product(models.Model):
	name = models.CharField(max_length=200)
	price = models.FloatField()
	digital = models.BooleanField(default=False,null=True, blank=True)
	image = models.ImageField(null=True, blank=True)

	def __str__(self):
		return self.name

	#if image not available 
	@property
	def imageURL(self):
		try:
			url = self.image.url   #.URL returns the publicly accessible URL of the file
		except:
			url = ''
		return url

class Order(models.Model):
	customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)   #Foreign key Customer can order many time many to one relationship 
	date_ordered = models.DateTimeField(auto_now_add=True)
	complete = models.BooleanField(default=False)
	transaction_id = models.CharField(max_length=100, null=True)

	def __str__(self):
		return str(self.id)
		
	@property
	def shipping(self):
		shipping = False
		orderitems = self.orderitem_set.all()  # you can access all related OrderItem objects using the orderitem_set attribute
		for i in orderitems:
			if i.product.digital == False: #order item class foreign key with order item orderitem hav product product.digital
				shipping = True
		return shipping

	@property
	def get_cart_total(self):
		orderitems = self.orderitem_set.all()
		total = sum([item.get_total for item in orderitems])
		return total

	@property
	def get_cart_items(self):
		orderitems = self.orderitem_set.all()
		total = sum([item.quantity for item in orderitems])
		return total 

class OrderItem(models.Model):
	product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
	order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
	quantity = models.IntegerField(default=0, null=True, blank=True)
	date_added = models.DateTimeField(auto_now_add=True)

	@property
	def get_total(self):
		total = self.product.price * self.quantity
		return total

class ShippingAddress(models.Model):
	customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
	order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
	address = models.CharField(max_length=200, null=False)
	city = models.CharField(max_length=200, null=False)
	state = models.CharField(max_length=200, null=False)
	zipcode = models.CharField(max_length=200, null=False)
	date_added = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.address
	
	@property
	def shipping(self):
		shipping = False
		orderitems = self.orderitem_set.all()
		for i in orderitems:
			if i.product.digital == False:
				shipping = True
		return shipping



# class favorites(models.Model):
# 	customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
# 	product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
	
# 	def __str__(self):
# 		return self.customer - self.product 

class Favourite(models.Model):
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE)
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percent = models.PositiveIntegerField()  # Discount in percentage
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def generate_code(self):
        length = 10
        characters = string.ascii_letters + string.digits
        code = ''.join(random.choice(characters) for _ in range(length))
        self.code = code

    def is_valid(self):
        return self.is_active and self.valid_from <= timezone.now() <= self.valid_to

    def __str__(self):
        return f'{self.code} - {self.discount_percent}% off'


