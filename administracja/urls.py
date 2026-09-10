from django.urls import path
from . import views

urlpatterns = [
    path('profil/', views.profil, name='profil'),
    path('uzytkownicy/', views.uzytkownicy, name='uzytkownicy'),
    path('uzytkownicy/dodaj/', views.dodaj_uzytkownika, name='dodaj_uzytkownika'),
    path('uzytkownicy/<int:pk>/', views.uzytkownik_szczegoly, name='uzytkownik_szczegoly'),
    path('uzytkownicy/<int:pk>/edytuj/', views.edytuj_uzytkownika, name='edytuj_uzytkownika'),
    path('oddzialy/', views.oddzialy, name='oddzialy'),
    path('oddzialy/dodaj/', views.dodaj_oddzial, name='dodaj_oddzial'),
    path('oddzialy/<int:pk>/', views.oddzial_szczegoly, name='oddzial_szczegoly'),
    path('oddzialy/<int:pk>/edytuj/', views.edytuj_oddzial, name='edytuj_oddzial'),
    path('api/uklady/', views.uklady_lista, name='uklady_lista'),
    path('api/uklady/zapisz/', views.uklady_zapisz, name='uklady_zapisz'),
    path('api/uklady/usun/', views.uklady_usun, name='uklady_usun'),
    path('api/uklady/aktywuj/', views.uklady_aktywuj, name='uklady_aktywuj'),
]