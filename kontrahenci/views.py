from django.shortcuts import render, redirect, get_object_or_404
from .models import Kontrahent, UzytkownikPojazdu
from django.contrib import messages

from .forms import KontrahentForm, UzytkownikPojazduForm, DodatkoweKontaktyFormSet
from flota_project.wspolne import widok_szczegolow, url_usuwania
from administracja.uprawnienia import OPERACJE, wymaga


def adres_tekst(obj):
    dom = ' '.join(filter(None, [obj.ulica, obj.numer_domu]))
    if dom and obj.numer_mieszkania:
        dom = f"{dom}/{obj.numer_mieszkania}"
    return ', '.join(filter(None, [dom, ' '.join(filter(None, [obj.kod_pocztowy, obj.miasto])), obj.kraj])) or None


def kontrahenci(request):
    kontrahenci = Kontrahent.objects.all().select_related('opiekun')
    template = 'kontrahenci/kontrahenci_view.html' if request.headers.get('HX-Request') else 'kontrahenci/kontrahenci.html'
    return render(request, template, {'kontrahenci': kontrahenci})


def _formularz_kontrahenta(request, kontrahent=None):
    """Wspolna obsluga dodawania i edycji wraz z dodatkowymi kontaktami."""
    if request.method == 'POST':
        form = KontrahentForm(request.POST, instance=kontrahent)
        formset = DodatkoweKontaktyFormSet(request.POST, instance=kontrahent)
        if form.is_valid() and formset.is_valid():
            obiekt = form.save()
            formset.instance = obiekt
            formset.save()
            messages.success(request, f'Zapisano kontrahenta: {obiekt.nazwa_firmy}.')
            return redirect('kontrahent_szczegoly', pk=obiekt.pk)
    else:
        form = KontrahentForm(instance=kontrahent)
        formset = DodatkoweKontaktyFormSet(instance=kontrahent)

    return render(request, 'kontrahenci/dodaj_kontrahenta.html', {
        'form': form,
        'formset': formset,
        'tytul': f'Edytuj kontrahenta: {kontrahent.nazwa_firmy}' if kontrahent else 'Dodaj kontrahenta',
        'przycisk': 'Zapisz zmiany' if kontrahent else 'Zapisz',
    })


@wymaga(OPERACJE)
def dodaj_kontrahenta(request):
    return _formularz_kontrahenta(request)


def kontrahent_szczegoly(request, pk):
    k = get_object_or_404(Kontrahent.objects.select_related('opiekun'), pk=pk)
    typy = [label for pole, label in [
        (k.typ_klient, 'Klient'), (k.typ_broker, 'Broker'), (k.typ_dealer, 'Dealer'),
        (k.typ_dostawca_finansowania, 'Dostawca finansowania'),
        (k.typ_obsluga_serwisowa, 'Obsługa serwisowa'), (k.typ_serwis, 'Serwis'),
        (k.typ_wlasciciel_pojazdow, 'Właściciel pojazdów'),
    ] if pole]
    sekcje = [
        {'naglowek': 'Dane firmy', 'pola': [
            ('Nazwa firmy', k.nazwa_firmy),
            ('Stan', k.get_stan_display()),
            ('Typ', ', '.join(typy) or None),
            ('Rodzaj działalności', k.get_rodzaj_dzialalnosci_display() if k.rodzaj_dzialalnosci else None),
            ('NIP', k.nip),
            ('REGON', k.regon),
            ('KRS', k.numer_krs),
            ('Opiekun klienta', k.opiekun.get_full_name() if k.opiekun else None),
        ]},
        {'naglowek': 'Kontakt i adres', 'pola': [
            ('Telefon', k.telefon),
            ('Email', k.email),
            ('Email do faktur', k.email_faktury),
            ('Adres', adres_tekst(k)),
            ('Województwo', k.wojewodztwo),
            ('Uwagi', k.uwagi),
        ]},
    ]
    kontakty = list(k.dodatkowe_kontakty.all())
    if kontakty:
        sekcje.append({'naglowek': 'Dodatkowe dane kontaktowe', 'pola': [
            (f"{kontakt.get_typ_display()}{f' ({kontakt.opis})' if kontakt.opis else ''}", kontakt.wartosc)
            for kontakt in kontakty
        ]})

    rezerwacje = list(k.rezerwacje.select_related('pojazd', 'klasa_pojazdu')[:10])
    if rezerwacje:
        sekcje.append({'naglowek': f'Rezerwacje ({k.rezerwacje.count()})', 'pola': [
            (
                f'{r.numer} · {r.get_status_display()}',
                f'{r.planowana_data_wydania:%d.%m.%Y} – {r.planowana_data_zwrotu:%d.%m.%Y}, '
                f'{r.pojazd.numer_rejestracyjny if r.pojazd else r.klasa_pojazdu}',
                f'/rezerwacje/{r.pk}/',
            ) for r in rezerwacje
        ]})

    cenniki = list(k.cenniki.all())
    if cenniki:
        sekcje.append({'naglowek': 'Cenniki', 'pola': [
            (c.nazwa, f'{c.get_typ_stawki_display()}, {c.waluta}', f'/cenniki/{c.pk}/') for c in cenniki
        ]})

    return widok_szczegolow(request, k.nazwa_firmy, sekcje, f'/kontrahenci/{pk}/edytuj/', '/kontrahenci/', usun_url=url_usuwania('kontrahent', pk), uprawnienie_edycji=OPERACJE)


@wymaga(OPERACJE)
def edytuj_kontrahenta(request, pk):
    return _formularz_kontrahenta(request, get_object_or_404(Kontrahent, pk=pk))


def uzytkownicy_pojazdow(request):
    uzytkownicy = UzytkownikPojazdu.objects.all()
    template = 'kontrahenci/uzytkownicy_pojazdow_view.html' if request.headers.get('HX-Request') else 'kontrahenci/uzytkownicy_pojazdow.html'
    return render(request, template, {'uzytkownicy': uzytkownicy})


@wymaga(OPERACJE)
def dodaj_uzytkownika_pojazdu(request):
    if request.method == 'POST':
        form = UzytkownikPojazduForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('uzytkownicy_pojazdow')
    else:
        form = UzytkownikPojazduForm()
    return render(request, 'kontrahenci/dodaj_uzytkownika_pojazdu.html', {'form': form})


def uzytkownik_pojazdu_szczegoly(request, pk):
    u = get_object_or_404(UzytkownikPojazdu, pk=pk)
    sekcje = [
        {'naglowek': 'Dane osobowe', 'pola': [
            ('Imię', u.imie),
            ('Nazwisko', u.nazwisko),
            ('PESEL', u.pesel),
            ('Telefon', u.telefon),
            ('Email', u.email),
            ('Adres', adres_tekst(u)),
        ]},
        {'naglowek': 'Dokumenty', 'pola': [
            ('Numer dokumentu', u.numer_dokumentu),
            ('Numer prawa jazdy', u.numer_prawa_jazdy),
            ('Ważność prawa jazdy', u.data_waznosci_prawa_jazdy),
        ]},
    ]
    return widok_szczegolow(request, f'{u.imie} {u.nazwisko}', sekcje, f'/uzytkownicy-pojazdow/{pk}/edytuj/', '/uzytkownicy-pojazdow/', usun_url=url_usuwania('uzytkownik-pojazdu', pk), uprawnienie_edycji=OPERACJE)


@wymaga(OPERACJE)
def edytuj_uzytkownika_pojazdu(request, pk):
    uzytkownik = get_object_or_404(UzytkownikPojazdu, pk=pk)
    if request.method == 'POST':
        form = UzytkownikPojazduForm(request.POST, instance=uzytkownik)
        if form.is_valid():
            form.save()
            return redirect('uzytkownicy_pojazdow')
    else:
        form = UzytkownikPojazduForm(instance=uzytkownik)
    return render(request, 'kontrahenci/dodaj_uzytkownika_pojazdu.html', {'form': form, 'tytul': f'Edytuj użytkownika: {uzytkownik}', 'przycisk': 'Zapisz zmiany'})
