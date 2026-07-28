from django.urls import path
from . import views

urlpatterns = [
    path('kontrahenci/', views.kontrahenci, name='kontrahenci'),
    path('kontrahenci/dodaj/', views.dodaj_kontrahenta, name='dodaj_kontrahenta'),
    path('kontrahenci/<int:pk>/', views.kontrahent_szczegoly, name='kontrahent_szczegoly'),
    path('kontrahenci/<int:pk>/edytuj/', views.edytuj_kontrahenta, name='edytuj_kontrahenta'),
    path('uzytkownicy-pojazdow/', views.uzytkownicy_pojazdow, name='uzytkownicy_pojazdow'),
    path('uzytkownicy-pojazdow/dodaj/', views.dodaj_uzytkownika_pojazdu, name='dodaj_uzytkownika_pojazdu'),
    path('uzytkownicy-pojazdow/<int:pk>/', views.uzytkownik_pojazdu_szczegoly, name='uzytkownik_pojazdu_szczegoly'),
    path('uzytkownicy-pojazdow/<int:pk>/edytuj/', views.edytuj_uzytkownika_pojazdu, name='edytuj_uzytkownika_pojazdu'),
]
