from django.urls import path, include, re_path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("contact", views.contact, name="contact"),
    path("login", views.login, name="login"),
    path("registration", views.registration, name="registration"),
    path("login", views.login, name="login"),
    path("logout", views.logout, name="logout"),
]