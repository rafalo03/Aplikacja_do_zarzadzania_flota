from django.shortcuts import render, redirect, get_object_or_404
from .models import Rezerwacja, Cennik
from .forms import RezerwacjaForm, CennikForm, PozycjaCennikaFormSet, ZmianaPojazduFormSet
from pojazdy.models import Pojazd
from serwis.views import widok_szczegolow, tak_nie


def pojazdy_do_wyboru():
    return Pojazd.objects.select_related('konfiguracja__model__marka', 'konfiguracja__klasa_pojazdu', 'oddzial')


def rezerwacje(request):
    rezerwacje = Rezerwacja.objects.all().select_related('klient', 'uzytkownik_pojazdu', 'klasa_pojazdu', 'pojazd')
    template = 'wynajmy/rezerwacje_view.html' if request.headers.get('HX-Request') else 'wynajmy/rezerwacje.html'
    return render(request, template, {'rezerwacje': rezerwacje})


def dodaj_rezerwacje(request):
    if request.method == 'POST':
        form = RezerwacjaForm(request.POST)
        formset = ZmianaPojazduFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            rezerwacja = form.save()
            formset.instance = rezerwacja
            formset.save()
            return redirect('rezerwacje')
    else:
        form = RezerwacjaForm()
        formset = ZmianaPojazduFormSet()
    return render(request, 'wynajmy/dodaj_rezerwacje.html', {'form': form, 'formset': formset, 'pojazdy': pojazdy_do_wyboru()})


def rezerwacja_szczegoly(request, pk):
    r = get_object_or_404(
        Rezerwacja.objects.select_related('klient', 'uzytkownik_pojazdu', 'klasa_pojazdu', 'pojazd', 'cennik'),
        pk=pk,
    )
    sekcje = [
        {'naglowek': 'Dane rezerwacji', 'pola': [
            ('Status', r.get_status_display()),
            ('Typ', r.get_typ_display()),
            ('Klient', str(r.klient), f'/kontrahenci/{r.klient_id}/'),
            ('Użytkownik pojazdu', str(r.uzytkownik_pojazdu), f'/uzytkownicy-pojazdow/{r.uzytkownik_pojazdu_id}/'),
            ('MPK klienta', r.mpk_klienta),
            ('Data utworzenia', r.data_utworzenia),
        ]},
        {'naglowek': 'Pojazd i cena', 'pola': [
            ('Klasa pojazdu', str(r.klasa_pojazdu)),
            ('Pojazd', str(r.pojazd) if r.pojazd else None, f'/pojazdy/{r.pojazd_id}/' if r.pojazd_id else None),
            ('Cennik', str(r.cennik) if r.cennik else None, f'/cenniki/{r.cennik_id}/' if r.cennik_id else None),
            ('Cena jednostkowa', f'{r.cena_jednostkowa} {r.waluta}' if r.cena_jednostkowa is not None else None),
        ]},
        {'naglowek': 'Wydanie', 'pola': [
            ('Planowana data wydania', r.planowana_data_wydania),
            ('Oddział wydania', r.oddzial_wydania),
            ('Podstawienie', tak_nie(r.podstawienie)),
            ('Adres podstawienia', r.adres_podstawienia),
        ]},
        {'naglowek': 'Zwrot', 'pola': [
            ('Planowana data zwrotu', r.planowana_data_zwrotu),
            ('Taki sam adres zwrotu', tak_nie(r.taki_sam_adres_zwrotu)),
            ('Adres zwrotu', r.adres_zwrotu),
            ('Uwagi do zwrotu', r.uwagi_zwrot),
        ]},
        {'naglowek': 'Uwagi', 'pola': [
            ('Uwagi', r.uwagi),
            ('Uwagi do faktury', r.uwagi_faktura),
        ]},
    ]
    zmiany = list(r.zmiany_pojazdu.select_related('pojazd__konfiguracja__model__marka'))
    if zmiany:
        sekcje.insert(2, {'naglowek': 'Zamiany pojazdu', 'pola': [
            (f'Od {z.data_zamiany:%d.%m.%Y %H:%M}', str(z.pojazd), f'/pojazdy/{z.pojazd_id}/') for z in zmiany
        ]})
    return widok_szczegolow(request, f'Rezerwacja #{r.pk}', sekcje, f'/rezerwacje/{pk}/edytuj/', '/rezerwacje/')


def edytuj_rezerwacje(request, pk):
    rezerwacja = get_object_or_404(Rezerwacja, pk=pk)
    if request.method == 'POST':
        form = RezerwacjaForm(request.POST, instance=rezerwacja)
        formset = ZmianaPojazduFormSet(request.POST, instance=rezerwacja)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('rezerwacje')
    else:
        form = RezerwacjaForm(instance=rezerwacja)
        formset = ZmianaPojazduFormSet(instance=rezerwacja)
    return render(request, 'wynajmy/dodaj_rezerwacje.html', {'form': form, 'formset': formset, 'pojazdy': pojazdy_do_wyboru(), 'tytul': f'Edytuj rezerwację #{rezerwacja.pk}', 'przycisk': 'Zapisz zmiany'})


def cenniki(request):
    cenniki = Cennik.objects.all().select_related('kontrahent')
    template = 'wynajmy/cenniki_view.html' if request.headers.get('HX-Request') else 'wynajmy/cenniki.html'
    return render(request, template, {'cenniki': cenniki})


def dodaj_cennik(request):
    if request.method == 'POST':
        form = CennikForm(request.POST)
        formset = PozycjaCennikaFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            cennik = form.save()
            formset.instance = cennik
            formset.save()
            return redirect('cenniki')
    else:
        form = CennikForm()
        formset = PozycjaCennikaFormSet()
    return render(request, 'wynajmy/dodaj_cennik.html', {'form': form, 'formset': formset})


def cennik_szczegoly(request, pk):
    c = get_object_or_404(Cennik.objects.select_related('kontrahent'), pk=pk)
    pozycje = c.pozycje.select_related('klasa_pojazdu')
    sekcje = [
        {'naglowek': 'Dane cennika', 'pola': [
            ('Nazwa', c.nazwa),
            ('Firma', str(c.kontrahent) if c.kontrahent else 'Standardowy', f'/kontrahenci/{c.kontrahent_id}/' if c.kontrahent_id else None),
            ('Typ stawki', c.get_typ_stawki_display()),
            ('Waluta', c.waluta),
            ('Aktywny', tak_nie(c.aktywny)),
        ]},
        {'naglowek': 'Pozycje cennika', 'pola': [
            (str(p.klasa_pojazdu), f'{p.cena} {c.waluta}') for p in pozycje
        ] or [('Pozycje', 'Brak pozycji')]},
    ]
    return widok_szczegolow(request, f'Cennik: {c.nazwa}', sekcje, f'/cenniki/{pk}/edytuj/', '/cenniki/')


def edytuj_cennik(request, pk):
    cennik = get_object_or_404(Cennik, pk=pk)
    if request.method == 'POST':
        form = CennikForm(request.POST, instance=cennik)
        formset = PozycjaCennikaFormSet(request.POST, instance=cennik)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('cenniki')
    else:
        form = CennikForm(instance=cennik)
        formset = PozycjaCennikaFormSet(instance=cennik)
    return render(request, 'wynajmy/dodaj_cennik.html', {'form': form, 'formset': formset, 'tytul': f'Edytuj cennik: {cennik.nazwa}', 'przycisk': 'Zapisz zmiany'})
