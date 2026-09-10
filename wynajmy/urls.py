from django.urls import path
from . import views

urlpatterns = [
    path('rezerwacje/', views.rezerwacje, name='rezerwacje'),
    path('rezerwacje/kalendarz/', views.kalendarz, name='kalendarz_rezerwacji'),
    path('rezerwacje/dodaj/', views.dodaj_rezerwacje, name='dodaj_rezerwacje'),
    path('rezerwacje/<int:pk>/', views.rezerwacja_szczegoly, name='rezerwacja_szczegoly'),
    path('rezerwacje/<int:pk>/edytuj/', views.edytuj_rezerwacje, name='edytuj_rezerwacje'),
    path('rezerwacje/<int:pk>/wydanie/', views.wydanie_rezerwacji, name='wydanie_rezerwacji'),
    path('rezerwacje/<int:pk>/zwrot/', views.zwrot_rezerwacji, name='zwrot_rezerwacji'),
    path('rezerwacje/<int:pk>/anuluj/', views.anuluj_rezerwacje, name='anuluj_rezerwacje'),
    path('api/wycena/', views.api_wycena, name='api_wycena'),
    path('api/dostepnosc/', views.api_dostepnosc, name='api_dostepnosc'),
    path('cenniki/', views.cenniki, name='cenniki'),
    path('cenniki/dodaj/', views.dodaj_cennik, name='dodaj_cennik'),
    path('cenniki/<int:pk>/', views.cennik_szczegoly, name='cennik_szczegoly'),
    path('cenniki/<int:pk>/edytuj/', views.edytuj_cennik, name='edytuj_cennik'),
]
