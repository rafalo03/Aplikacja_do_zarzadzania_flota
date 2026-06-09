from django.urls import path
from . import views

urlpatterns = [
    path('pojazdy/', views.pojazdy, name='pojazdy'),
    path('pojazdy/dodaj/', views.dodaj_pojazd, name='dodaj_pojazd'),
    path('polisy/', views.polisy, name='polisy'),
    path('polisy/dodaj/', views.dodaj_polise, name='dodaj_polise'),
]