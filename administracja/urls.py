from django.urls import path
from . import views

urlpatterns = [
    path('uzytkownicy/', views.uzytkownicy, name='uzytkownicy'),
    path('uzytkownicy/dodaj/', views.dodaj_uzytkownika, name='dodaj_uzytkownika'),
]