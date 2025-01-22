from django.urls import path # type: ignore
from . import views
from django.urls import path # type: ignore

#"url paths" to call these views.
urlpatterns = [
    path('',views.store, name="store"),
    path('cart/',views.cart, name="cart"),
    path('checkout/',views.checkout, name="checkout"),

    path('favviewpage/', views.favPage, name='favviewpage'),  # Favorites view page
    path('updateFavorite/', views.updateFavorite, name='updateFavorite'),  # Add to favorites
    path('removeFavorite/<int:id>/', views.removeFavorite, name='removeFavorite'),

    path('update_item/',views.updateItem, name="UpdateItem"),
    path('process_order/',views.processorder,name="process_order"),

    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
   
    path('profile/<str:username>/', views.profile, name='profile'),

    # path('product_details/<int:product_id>/', views.profile, name='profile'),
    

]