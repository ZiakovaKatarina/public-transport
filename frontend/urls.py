from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.hladanie_spojeni, name='index'),
    path('hladanie-spojeni', views.hladanie_spojeni, name='hladanie-spojeni'),
    path('prihlasenie', views.prihlasenie, name='prihlasenie'),
    path('odhlasenie', auth_views.LogoutView.as_view(), name='odhlasenie'),
    path('nahravanie_udajov', views.nahravanie_udajov, name='nahravanie_udajov')

]