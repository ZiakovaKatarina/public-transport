from django.urls import path
from . import views

app_name = "data_management"

urlpatterns = [
    path("load_files", views.load_files, name="load_files"),
    path("search_connections", views.search_connections, name="search_connections"),
    path('calculate_distance', views.calculate_distance, name='calculate_distance'),
    path('suradnice_mhd_trasy', views.suradnice_mhd_trasy, name='suradnice_mhd_trasy'),
    path('zisti_adresu', views.zisti_adresu, name='zisti_adresu'),
]