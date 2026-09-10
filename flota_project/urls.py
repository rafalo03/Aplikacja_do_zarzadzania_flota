import datetime

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from pojazdy.models import Pojazd, Polisa
from kontrahenci.models import Kontrahent
from wynajmy.models import Rezerwacja
from .wspolne import usun_obiekt
from administracja.uprawnienia import filtruj_pojazdy, filtruj_po_pojezdzie, filtruj_rezerwacje

@ensure_csrf_cookie
def dashboard(request):
    teraz = timezone.now()
    dzis = timezone.localdate()
    za_tydzien = teraz + datetime.timedelta(days=7)

    rezerwacje = filtruj_rezerwacje(
        Rezerwacja.objects.select_related('klient', 'pojazd', 'klasa_pojazdu'), request.user
    )
    pojazdy = filtruj_pojazdy(Pojazd.objects.all(), request.user)
    polisy = filtruj_po_pojezdzie(Polisa.objects.all(), request.user)

    context = {
        'liczba_pojazdow': pojazdy.count(),
        'liczba_dostepnych': pojazdy.filter(status='dostepny').count(),
        'liczba_wynajetych': pojazdy.filter(status='wynajety').count(),
        'liczba_w_serwisie': pojazdy.filter(status='serwis').count(),
        'liczba_polis': polisy.count(),
        'liczba_kontrahentow': Kontrahent.objects.count(),
        'liczba_rezerwacji': rezerwacje.filter(status__in=Rezerwacja.STATUSY_BLOKUJACE).count(),
        'nadchodzace_wydania': rezerwacje.filter(
            status__in=('nowa', 'potwierdzona'),
            planowana_data_wydania__range=(teraz, za_tydzien),
        ).order_by('planowana_data_wydania')[:5],
        'nadchodzace_zwroty': rezerwacje.filter(
            status='w_toku',
            planowana_data_zwrotu__lte=za_tydzien,
        ).order_by('planowana_data_zwrotu')[:5],
        'opoznione': rezerwacje.filter(status='w_toku', planowana_data_zwrotu__lt=teraz)
                               .order_by('planowana_data_zwrotu')[:5],
        'wygasajace_polisy': polisy.select_related('pojazd').filter(
            data_do__range=(dzis, dzis + datetime.timedelta(days=30)),
        ).order_by('data_do')[:5],
    }
    template = 'dashboard_view.html' if request.headers.get('HX-Request') else 'dashboard.html'
    return render(request, template, context)

def wyloguj_do_aplikacji(request):
    auth_logout(request)
    return redirect('login')

class LogowanieView(auth_views.LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        if not self.request.POST.get('remember_me'):
            self.request.session.set_expiry(0)
        return super().form_valid(form)

urlpatterns = [
    path('admin/logout/', wyloguj_do_aplikacji),
    path('admin/', admin.site.urls),
    path('login/', LogowanieView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', dashboard, name='dashboard'),
    path('usun/<slug:typ>/<int:pk>/', usun_obiekt, name='usun_obiekt'),
    path('', include('pojazdy.urls')),
    path('', include('administracja.urls')),
    path('', include('serwis.urls')),
    path('', include('kontrahenci.urls')),
    path('', include('wynajmy.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)