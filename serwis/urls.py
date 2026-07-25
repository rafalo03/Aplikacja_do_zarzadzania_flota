from django.urls import path
from . import views

urlpatterns = [
    path('zlecenia/', views.zlecenia, name='zlecenia'),
    path('zlecenia/dodaj/', views.dodaj_zlecenie, name='dodaj_zlecenie'),
    path('szkody/', views.szkody, name='szkody'),
    path('szkody/dodaj/', views.dodaj_szkode, name='dodaj_szkode'),
    path('uszkodzenia/', views.uszkodzenia, name='uszkodzenia'),
]