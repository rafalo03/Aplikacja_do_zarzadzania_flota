import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .forms import UzytkownikForm, OddzialForm, EdytujUzytkownikaForm
from .models import UkladTabeli, Oddzial

def uzytkownicy(request):
    uzytkownicy = User.objects.all()
    template = 'administracja/uzytkownicy_view.html' if request.headers.get('HX-Request') else 'administracja/uzytkownicy.html'
    return render(request, template, {'uzytkownicy': uzytkownicy})

def dodaj_uzytkownika(request):
    if request.method == 'POST':
        form = UzytkownikForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('uzytkownicy')
    else:
        form = UzytkownikForm()
    return render(request, 'administracja/dodaj_uzytkownika.html', {'form': form})

def oddzialy(request):
    oddzialy = Oddzial.objects.all()
    template = 'administracja/oddzialy_view.html' if request.headers.get('HX-Request') else 'administracja/oddzialy.html'
    return render(request, template, {'oddzialy': oddzialy})

def dodaj_oddzial(request):
    if request.method == 'POST':
        form = OddzialForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('oddzialy')
    else:
        form = OddzialForm()
    return render(request, 'administracja/dodaj_oddzial.html', {'form': form})

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

def widok_szczegolow(request, tytul, sekcje, edytuj_url=None, powrot_url=None):
    template = 'szczegoly_view.html' if request.headers.get('HX-Request') else 'szczegoly.html'
    return render(request, template, {'tytul': tytul, 'sekcje': sekcje, 'edytuj_url': edytuj_url, 'powrot_url': powrot_url})

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
    return widok_szczegolow(request, f'Oddział — {oddzial.nazwa}', sekcje, f'/oddzialy/{pk}/edytuj/', '/oddzialy/')

def uzytkownik_szczegoly(request, pk):
    uzytkownik = get_object_or_404(User, pk=pk)
    telefon = uzytkownik.profil.telefon if hasattr(uzytkownik, 'profil') else None
    sekcje = [{'naglowek': 'Dane użytkownika', 'pola': [
        ('Login', uzytkownik.username),
        ('Imię i nazwisko', uzytkownik.get_full_name()),
        ('Email', uzytkownik.email),
        ('Telefon', telefon),
        ('Administrator', 'Tak' if uzytkownik.is_superuser else 'Nie'),
        ('Aktywny', 'Tak' if uzytkownik.is_active else 'Nie'),
        ('Data dołączenia', uzytkownik.date_joined.strftime('%Y-%m-%d')),
        ('Ostatnie logowanie', uzytkownik.last_login.strftime('%Y-%m-%d %H:%M') if uzytkownik.last_login else None),
    ]}]
    return widok_szczegolow(request, f'Użytkownik — {uzytkownik.username}', sekcje, f'/uzytkownicy/{pk}/edytuj/', '/uzytkownicy/')

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
