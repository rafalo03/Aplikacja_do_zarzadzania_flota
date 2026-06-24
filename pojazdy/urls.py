from django.urls import path
from . import views

urlpatterns = [
    path('pojazdy/', views.pojazdy, name='pojazdy'),
    path('pojazdy/dodaj/', views.dodaj_pojazd, name='dodaj_pojazd'),
    path('polisy/', views.polisy, name='polisy'),
    path('polisy/dodaj/', views.dodaj_polise, name='dodaj_polise'),
    path('marki/', views.marki, name='marki'),
    path('marki/dodaj/', views.dodaj_marke, name='dodaj_marke'),
    path('modele/', views.modele, name='modele'),
    path('modele/dodaj/', views.dodaj_model, name='dodaj_model'),
    path('klasy/', views.klasy, name='klasy'),
    path('klasy/dodaj/', views.dodaj_klase, name='dodaj_klase'),
]