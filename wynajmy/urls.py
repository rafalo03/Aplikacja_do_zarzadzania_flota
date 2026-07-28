from django.urls import path
from . import views

urlpatterns = [
    path('rezerwacje/', views.rezerwacje, name='rezerwacje'),
    path('rezerwacje/dodaj/', views.dodaj_rezerwacje, name='dodaj_rezerwacje'),
    path('rezerwacje/<int:pk>/', views.rezerwacja_szczegoly, name='rezerwacja_szczegoly'),
    path('rezerwacje/<int:pk>/edytuj/', views.edytuj_rezerwacje, name='edytuj_rezerwacje'),
    path('cenniki/', views.cenniki, name='cenniki'),
    path('cenniki/dodaj/', views.dodaj_cennik, name='dodaj_cennik'),
    path('cenniki/<int:pk>/', views.cennik_szczegoly, name='cennik_szczegoly'),
    path('cenniki/<int:pk>/edytuj/', views.edytuj_cennik, name='edytuj_cennik'),
]
