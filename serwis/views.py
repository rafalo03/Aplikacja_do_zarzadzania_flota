from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404

from .models import ZlecenieSerwisowe, SzkodaBladcharska, Uszkodzenie
from .forms import ZlecenieSerwisoweForms, SzkodaBlacharskaForm, UszkodzenieForm
from flota_project.wspolne import widok_szczegolow, tak_nie, url_usuwania
from administracja.uprawnienia import OPERACJE, wymaga, filtruj_po_pojezdzie, widzi_pojazd


def _filtruj(lista, request, pola_szukania):
    """Wspolne filtrowanie list serwisowych: status, pojazd i wyszukiwarka."""
    status = request.GET.get('status', '')
    szukaj = request.GET.get('szukaj', '')
    pojazd = request.GET.get('pojazd', '')

    if status:
        lista = lista.filter(status=status)
    if pojazd:
        lista = lista.filter(pojazd_id=pojazd)
    if szukaj:
        warunek = Q()
        for pole in pola_szukania:
            warunek |= Q(**{f'{pole}__icontains': szukaj})
        lista = lista.filter(warunek)
    return lista, {'status': status, 'szukaj': szukaj, 'pojazd': pojazd}


def zlecenia(request):
    lista = filtruj_po_pojezdzie(ZlecenieSerwisowe.objects.select_related('pojazd', 'warsztat'), request.user)
    lista, filtry = _filtruj(lista, request, ['pojazd__numer_rejestracyjny', 'opis', 'warsztat__nazwa_firmy'])
    kontekst = {'zlecenia': lista, 'statusy': ZlecenieSerwisowe.STATUS, **filtry}
    template = 'serwis/zlecenia_view.html' if request.headers.get('HX-Request') else 'serwis/zlecenia.html'
    return render(request, template, kontekst)


def _formularz_zlecenia(request, zlecenie=None):
    if request.method == 'POST':
        form = ZlecenieSerwisoweForms(request.POST, uzytkownik=request.user, instance=zlecenie)
        if form.is_valid():
            obiekt = form.save()
            messages.success(request, f'Zapisano zlecenie serwisowe #{obiekt.pk}.')
            return redirect('zlecenie_szczegoly', pk=obiekt.pk)
    else:
        form = ZlecenieSerwisoweForms(uzytkownik=request.user, instance=zlecenie, initial=_wynajem_pojazdu(request))
    return render(request, 'serwis/dodaj_zlecenie.html', {
        'form': form,
        'tytul': f'Edytuj zlecenie #{zlecenie.pk}' if zlecenie else 'Dodaj zlecenie',
        'przycisk': 'Zapisz zmiany' if zlecenie else 'Zapisz',
    })


def _wynajem_pojazdu(request):
    """Podpowiada pojazd z adresu i najemcę z jego trwającej rezerwacji."""
    pojazd_id = request.GET.get('pojazd')
    if not pojazd_id:
        return {}
    from wynajmy.models import Rezerwacja

    initial = {'pojazd': pojazd_id}
    trwajaca = Rezerwacja.objects.filter(pojazd_id=pojazd_id, status='w_toku').select_related('klient').first()
    if trwajaca:
        initial['w_trakcie_wynajmu'] = True
        initial['najemca'] = trwajaca.klient_id
    return initial


@wymaga(OPERACJE)
def dodaj_zlecenie(request):
    return _formularz_zlecenia(request)


def szkody(request):
    lista = filtruj_po_pojezdzie(SzkodaBladcharska.objects.select_related('pojazd', 'warsztat'), request.user)
    lista, filtry = _filtruj(lista, request, ['pojazd__numer_rejestracyjny', 'numer_szkody', 'opis'])
    kontekst = {'szkody': lista, 'statusy': SzkodaBladcharska.STATUS, **filtry}
    template = 'serwis/szkody_view.html' if request.headers.get('HX-Request') else 'serwis/szkody.html'
    return render(request, template, kontekst)


def _formularz_szkody(request, szkoda=None):
    if request.method == 'POST':
        form = SzkodaBlacharskaForm(request.POST, uzytkownik=request.user, instance=szkoda)
        if form.is_valid():
            obiekt = form.save()
            messages.success(request, f'Zapisano szkodę #{obiekt.pk}.')
            return redirect('szkoda_szczegoly', pk=obiekt.pk)
    else:
        form = SzkodaBlacharskaForm(uzytkownik=request.user, instance=szkoda, initial=_wynajem_pojazdu(request))
    return render(request, 'serwis/dodaj_szkode.html', {
        'form': form,
        'tytul': f'Edytuj szkodę #{szkoda.pk}' if szkoda else 'Dodaj szkodę',
        'przycisk': 'Zapisz zmiany' if szkoda else 'Zapisz',
    })


@wymaga(OPERACJE)
def dodaj_szkode(request):
    return _formularz_szkody(request)


def uszkodzenia(request):
    lista = filtruj_po_pojezdzie(Uszkodzenie.objects.select_related('pojazd'), request.user)
    szukaj = request.GET.get('szukaj', '')
    naprawione = request.GET.get('naprawione', '')
    pojazd = request.GET.get('pojazd', '')

    if pojazd:
        lista = lista.filter(pojazd_id=pojazd)
    if naprawione in ('tak', 'nie'):
        lista = lista.filter(naprawione=(naprawione == 'tak'))
    if szukaj:
        lista = lista.filter(
            Q(pojazd__numer_rejestracyjny__icontains=szukaj)
            | Q(opis__icontains=szukaj)
            | Q(zglaszajacy__icontains=szukaj)
        )

    kontekst = {'uszkodzenia': lista, 'szukaj': szukaj, 'naprawione': naprawione, 'pojazd': pojazd}
    template = 'serwis/uszkodzenia_view.html' if request.headers.get('HX-Request') else 'serwis/uszkodzenia.html'
    return render(request, template, kontekst)


def _formularz_uszkodzenia(request, uszkodzenie=None):
    if request.method == 'POST':
        form = UszkodzenieForm(request.POST, request.FILES, instance=uszkodzenie, uzytkownik=request.user)
        if form.is_valid():
            obiekt = form.save()
            messages.success(request, f'Zapisano uszkodzenie #{obiekt.pk}.')
            return redirect('uszkodzenie_szczegoly', pk=obiekt.pk)
    else:
        initial = {'pojazd': request.GET.get('pojazd')} if request.GET.get('pojazd') else {}
        form = UszkodzenieForm(instance=uszkodzenie, initial=initial, uzytkownik=request.user)
    return render(request, 'serwis/dodaj_uszkodzenie.html', {
        'form': form,
        'tytul': f'Edytuj uszkodzenie #{uszkodzenie.pk}' if uszkodzenie else 'Zgłoś uszkodzenie',
        'przycisk': 'Zapisz zmiany' if uszkodzenie else 'Zapisz',
    })


@wymaga(OPERACJE)
def dodaj_uszkodzenie(request):
    return _formularz_uszkodzenia(request)

def zlecenie_szczegoly(request, pk):
    z = get_object_or_404(ZlecenieSerwisowe.objects.select_related('pojazd', 'najemca', 'warsztat'), pk=pk)
    if not widzi_pojazd(request.user, z.pojazd):
        raise Http404('Zlecenie dotyczy pojazdu z innego oddziału.')
    sekcje = [
        {'naglowek': 'Dane zlecenia', 'pola': [
            ('Pojazd', str(z.pojazd), f'/pojazdy/{z.pojazd_id}/'),
            ('Typ', z.get_typ_display()),
            ('Status', z.get_status_display()),
            ('Płatnik', z.get_platnik_display()),
            ('W trakcie wynajmu', tak_nie(z.w_trakcie_wynajmu)),
            ('Najemca', z.najemca),
            ('Warsztat', z.warsztat),
        ]},
        {'naglowek': 'Terminy i koszty', 'pola': [
            ('Data przyjęcia', z.data_przyjecia),
            ('Planowane zakończenie', z.planowana_data_zakonczenia),
            ('Przebieg', f'{z.przebieg} km' if z.przebieg is not None else None),
            ('Planowany koszt netto', z.planowany_koszt_netto),
            ('Rzeczywisty koszt netto', z.rzeczywisty_koszt_netto),
            ('Opis', z.opis),
        ]},
    ]
    return widok_szczegolow(
        request, f'Zlecenie serwisowe #{z.pk}', sekcje,
        f'/zlecenia/{pk}/edytuj/', '/zlecenia/',
        usun_url=url_usuwania('zlecenie', pk),
        uprawnienie_edycji=OPERACJE,
        odznaka={'tekst': z.get_status_display(), 'kolor': z.kolor_statusu},
    )

@wymaga(OPERACJE)
def edytuj_zlecenie(request, pk):
    return _formularz_zlecenia(request, get_object_or_404(ZlecenieSerwisowe, pk=pk))

def szkoda_szczegoly(request, pk):
    s = get_object_or_404(SzkodaBladcharska.objects.select_related('pojazd', 'najemca', 'warsztat'), pk=pk)
    if not widzi_pojazd(request.user, s.pojazd):
        raise Http404('Szkoda dotyczy pojazdu z innego oddziału.')
    sekcje = [
        {'naglowek': 'Dane szkody', 'pola': [
            ('Pojazd', str(s.pojazd), f'/pojazdy/{s.pojazd_id}/'),
            ('Numer szkody', s.numer_szkody),
            ('Status', s.get_status_display()),
            ('Płatnik', s.get_platnik_display()),
            ('W trakcie wynajmu', tak_nie(s.w_trakcie_wynajmu)),
            ('Najemca', s.najemca),
            ('Warsztat', s.warsztat),
        ]},
        {'naglowek': 'Zdarzenie i koszty', 'pola': [
            ('Data zdarzenia', s.data_zdarzenia),
            ('Przebieg', f'{s.przebieg} km' if s.przebieg is not None else None),
            ('Planowany koszt netto', s.planowany_koszt_netto),
            ('Rzeczywisty koszt netto', s.rzeczywisty_koszt_netto),
            ('Opis', s.opis),
        ]},
    ]
    return widok_szczegolow(
        request, f'Szkoda blacharska #{s.pk}', sekcje,
        f'/szkody/{pk}/edytuj/', '/szkody/',
        usun_url=url_usuwania('szkoda', pk),
        uprawnienie_edycji=OPERACJE,
        odznaka={'tekst': s.get_status_display(), 'kolor': s.kolor_statusu},
    )

@wymaga(OPERACJE)
def edytuj_szkode(request, pk):
    return _formularz_szkody(request, get_object_or_404(SzkodaBladcharska, pk=pk))

def uszkodzenie_szczegoly(request, pk):
    u = get_object_or_404(Uszkodzenie.objects.select_related('pojazd'), pk=pk)
    if not widzi_pojazd(request.user, u.pojazd):
        raise Http404('Uszkodzenie dotyczy pojazdu z innego oddziału.')
    sekcje = [{'naglowek': 'Dane uszkodzenia', 'pola': [
        ('Pojazd', str(u.pojazd), f'/pojazdy/{u.pojazd_id}/'),
        ('Data wykrycia', u.data_wykrycia),
        ('Zgłaszający', u.zglaszajacy),
        ('Naprawione', tak_nie(u.naprawione)),
        ('Koszt naprawy', u.koszt_naprawy),
        ('Zdjęcie', 'Otwórz zdjęcie' if u.zdjecie else None, u.zdjecie.url if u.zdjecie else None),
        ('Opis', u.opis),
    ]}]
    return widok_szczegolow(
        request, f'Uszkodzenie #{u.pk}', sekcje,
        f'/uszkodzenia/{pk}/edytuj/', '/uszkodzenia/',
        usun_url=url_usuwania('uszkodzenie', pk),
        uprawnienie_edycji=OPERACJE,
        odznaka={'tekst': u.status_opis, 'kolor': u.kolor_statusu},
    )

@wymaga(OPERACJE)
def edytuj_uszkodzenie(request, pk):
    return _formularz_uszkodzenia(request, get_object_or_404(Uszkodzenie, pk=pk))
