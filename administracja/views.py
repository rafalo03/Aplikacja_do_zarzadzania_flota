import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .forms import UzytkownikForm, OddzialForm, EdytujUzytkownikaForm, ProfilForm
from .models import UkladTabeli, Oddzial, ProfilUzytkownika
from flota_project.wspolne import widok_szczegolow, url_usuwania
from .uprawnienia import ADMINISTRACJA, rola, wymaga

@wymaga(ADMINISTRACJA)
def uzytkownicy(request):
    uzytkownicy = User.objects.all()
    template = 'administracja/uzytkownicy_view.html' if request.headers.get('HX-Request') else 'administracja/uzytkownicy.html'
    return render(request, template, {'uzytkownicy': uzytkownicy})

@wymaga(ADMINISTRACJA)
def dodaj_uzytkownika(request):
    if request.method == 'POST':
        form = UzytkownikForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('uzytkownicy')
    else:
        form = UzytkownikForm()
    return render(request, 'administracja/dodaj_uzytkownika.html', {'form': form})

@wymaga(ADMINISTRACJA)
def oddzialy(request):
    oddzialy = Oddzial.objects.all()
    template = 'administracja/oddzialy_view.html' if request.headers.get('HX-Request') else 'administracja/oddzialy.html'
    return render(request, template, {'oddzialy': oddzialy})

@wymaga(ADMINISTRACJA)
def dodaj_oddzial(request):
    if request.method == 'POST':
        form = OddzialForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('oddzialy')
    else:
        form = OddzialForm()
    return render(request, 'administracja/dodaj_oddzial.html', {'form': form})

@wymaga(ADMINISTRACJA)
def edytuj_oddzial(request, pk):
    oddzial = get_object_or_404(Oddzial, pk=pk)
    if request.method == 'POST':
        form = OddzialForm(request.POST, instance=oddzial)
        if form.is_valid():
            form.save()
            return redirect('oddzialy')
    else:
        form = OddzialForm(instance=oddzial)
    return render(request, 'administracja/edytuj_oddzial.html', {'form': form, 'oddzial': oddzial})

@login_required
def uklady_lista(request):
    tabela = request.GET.get('tabela', '')
    uklady = UkladTabeli.objects.filter(user=request.user, tabela=tabela)
    layouts = {u.nazwa: u.dane for u in uklady}
    active = next((u.nazwa for u in uklady if u.aktywny), None)
    return JsonResponse({'layouts': layouts, 'active': active})


@login_required
@require_POST
def uklady_zapisz(request):
    dane_req = json.loads(request.body)
    tabela = dane_req.get('tabela')
    nazwa = (dane_req.get('nazwa') or '').strip()[:100]
    dane = dane_req.get('dane')
    if not tabela or not nazwa or dane is None:
        return JsonResponse({'ok': False, 'blad': 'Brak nazwy lub danych układu'}, status=400)
    UkladTabeli.objects.filter(user=request.user, tabela=tabela, aktywny=True).update(aktywny=False)
    UkladTabeli.objects.update_or_create(
        user=request.user, tabela=tabela, nazwa=nazwa,
        defaults={'dane': dane, 'aktywny': True},
    )
    return JsonResponse({'ok': True})


@login_required
@require_POST
def uklady_usun(request):
    dane_req = json.loads(request.body)
    UkladTabeli.objects.filter(
        user=request.user, tabela=dane_req.get('tabela'), nazwa=dane_req.get('nazwa'),
    ).delete()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def uklady_aktywuj(request):
    dane_req = json.loads(request.body)
    tabela = dane_req.get('tabela')
    nazwa = dane_req.get('nazwa')
    UkladTabeli.objects.filter(user=request.user, tabela=tabela, aktywny=True).update(aktywny=False)
    if nazwa:
        UkladTabeli.objects.filter(user=request.user, tabela=tabela, nazwa=nazwa).update(aktywny=True)
    return JsonResponse({'ok': True})

@wymaga(ADMINISTRACJA)
def oddzial_szczegoly(request, pk):
    oddzial = get_object_or_404(Oddzial, pk=pk)
    pojazdy_oddzialu = ', '.join(p.numer_rejestracyjny for p in oddzial.pojazdy.all())
    sekcje = [{'naglowek': 'Dane oddziału', 'pola': [
        ('Nazwa', oddzial.nazwa),
        ('Adres', oddzial.adres),
        ('Telefon', oddzial.telefon),
        ('Liczba pojazdów', oddzial.pojazdy.count()),
        ('Pojazdy', pojazdy_oddzialu),
    ]}]
    return widok_szczegolow(request, f'Oddział — {oddzial.nazwa}', sekcje, f'/oddzialy/{pk}/edytuj/', '/oddzialy/', usun_url=url_usuwania('oddzial', pk), uprawnienie_edycji=ADMINISTRACJA)

@wymaga(ADMINISTRACJA)
def uzytkownik_szczegoly(request, pk):
    uzytkownik = get_object_or_404(User, pk=pk)
    profil = getattr(uzytkownik, 'profil', None)
    rola_uzytkownika = rola(uzytkownik)
    sekcje = [{'naglowek': 'Dane użytkownika', 'pola': [
        ('Login', uzytkownik.username),
        ('Imię i nazwisko', uzytkownik.get_full_name()),
        ('Email', uzytkownik.email),
        ('Telefon', profil.telefon if profil else None),
        ('Rola', dict(ProfilUzytkownika.ROLE).get(rola_uzytkownika, rola_uzytkownika)),
        ('Zakres uprawnień', ProfilUzytkownika.OPIS_ROL.get(rola_uzytkownika)),
        ('Oddział', str(profil.oddzial) if profil and profil.oddzial else 'Wszystkie oddziały'),
        ('Aktywny', 'Tak' if uzytkownik.is_active else 'Nie'),
        ('Data dołączenia', uzytkownik.date_joined.strftime('%Y-%m-%d')),
        ('Ostatnie logowanie', uzytkownik.last_login.strftime('%Y-%m-%d %H:%M') if uzytkownik.last_login else None),
    ]}]
    odznaka = {'tekst': dict(ProfilUzytkownika.ROLE).get(rola_uzytkownika, rola_uzytkownika),
               'kolor': 'akcent' if rola_uzytkownika == 'administrator' else 'neutralny'}
    return widok_szczegolow(request, f'Użytkownik — {uzytkownik.username}', sekcje, f'/uzytkownicy/{pk}/edytuj/', '/uzytkownicy/', usun_url=url_usuwania('uzytkownik', pk), uprawnienie_edycji=ADMINISTRACJA, odznaka=odznaka)

@login_required
def profil(request):
    """Wlasne konto: dane kontaktowe i zmiana hasla."""
    if request.method == 'POST' and 'zapisz_dane' in request.POST:
        form = ProfilForm(request.POST, instance=request.user)
        form_hasla = PasswordChangeForm(request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Zapisano dane konta.')
            return redirect('profil')
    elif request.method == 'POST' and 'zmien_haslo' in request.POST:
        form = ProfilForm(instance=request.user)
        form_hasla = PasswordChangeForm(request.user, request.POST)
        if form_hasla.is_valid():
            uzytkownik = form_hasla.save()
            update_session_auth_hash(request, uzytkownik)  # nie wylogowuj po zmianie
            messages.success(request, 'Hasło zostało zmienione.')
            return redirect('profil')
    else:
        form = ProfilForm(instance=request.user)
        form_hasla = PasswordChangeForm(request.user)

    return render(request, 'administracja/profil.html', {
        'form': form,
        'form_hasla': form_hasla,
    })


@wymaga(ADMINISTRACJA)
def edytuj_uzytkownika(request, pk):
    uzytkownik = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = EdytujUzytkownikaForm(request.POST, instance=uzytkownik)
        if form.is_valid():
            form.save()
            return redirect('uzytkownicy')
    else:
        form = EdytujUzytkownikaForm(instance=uzytkownik)
    return render(request, 'administracja/dodaj_uzytkownika.html', {'form': form, 'tytul': f'Edytuj użytkownika — {uzytkownik.username}', 'przycisk': 'Zapisz zmiany'})
