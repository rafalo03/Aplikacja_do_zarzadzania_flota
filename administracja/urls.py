from django.urls import path
from . import views

urlpatterns = [
    path('uzytkownicy/', views.uzytkownicy, name='uzytkownicy'),
    path('uzytkownicy/dodaj/', views.dodaj_uzytkownika, name='dodaj_uzytkownika'),
    path('api/uklady/', views.uklady_lista, name='uklady_lista'),
    path('api/uklady/zapisz/', views.uklady_zapisz, name='uklady_zapisz'),
    path('api/uklady/usun/', views.uklady_usun, name='uklady_usun'),
    path('api/uklady/aktywuj/', views.uklady_aktywuj, name='uklady_aktywuj'),
]