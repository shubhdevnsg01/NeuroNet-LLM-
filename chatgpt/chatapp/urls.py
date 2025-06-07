from django.urls import path
from . import views

urlpatterns = [
    path('signup/',views.signup,name='signup'),
    path('signin/',views.signin,name='signin'),
    path('',views.index,name='index'),
    path('signout/',views.signout,name='signout'),
    path('get-value',views.getValue,name='get-value')
]