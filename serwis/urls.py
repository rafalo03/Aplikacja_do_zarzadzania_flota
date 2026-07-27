from django.urls import path
from . import views

urlpatterns = [
    path('zlecenia/', views.zlecenia, name='zlecenia'),
    path('zlecenia/dodaj/', views.dodaj_zlecenie, name='dodaj_zlecenie'),
    path('zlecenia/<int:pk>/', views.zlecenie_szczegoly, name='zlecenie_szczegoly'),
    path('zlecenia/<int:pk>/edytuj/', views.edytuj_zlecenie, name='edytuj_zlecenie'),
    path('szkody/', views.szkody, name='szkody'),
    path('szkody/dodaj/', views.dodaj_szkode, name='dodaj_szkode'),
    path('szkody/<int:pk>/', views.szkoda_szczegoly, name='szkoda_szczegoly'),
    path('szkody/<int:pk>/edytuj/', views.edytuj_szkode, name='edytuj_szkode'),
    path('uszkodzenia/', views.uszkodzenia, name='uszkodzenia'),
    path('uszkodzenia/dodaj/', views.dodaj_uszkodzenie, name='dodaj_uszkodzenie'),
    path('uszkodzenia/<int:pk>/', views.uszkodzenie_szczegoly, name='uszkodzenie_szczegoly'),
    path('uszkodzenia/<int:pk>/edytuj/', views.edytuj_uszkodzenie, name='edytuj_uszkodzenie'),
]