from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from pojazdy.models import Pojazd
from pojazdy.models import Polisa
from kontrahenci.models import Kontrahent

def dashboard(request):
    context = {
        'liczba_pojazdow': Pojazd.objects.count(),
        'liczba_polis': Polisa.objects.count(),
        'liczba_kontrahentow': Kontrahent.objects.count(),
    }
    template = 'dashboard_view.html' if request.headers.get('HX-Request') else 'dashboard.html'
    return render(request, template, context)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),
    path('', include('pojazdy.urls')),
]