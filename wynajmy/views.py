import datetime
from decimal import Decimal

from django.contrib import messages
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import Rezerwacja, Cennik, znajdz_cennik
from .forms import (
    RezerwacjaForm, CennikForm, PozycjaCennikaFormSet, ZmianaPojazduFormSet,
    WydanieForm, ZwrotForm,
)
from pojazdy.models import Pojazd, KlasaPojazdu
from flota_project.wspolne import widok_szczegolow, tak_nie, url_usuwania
from administracja.uprawnienia import (
    OPERACJE, SLOWNIKI, wymaga, filtruj_pojazdy, filtruj_rezerwacje, widzi_rezerwacje,
)


def pojazdy_do_wyboru(user):
    return filtruj_pojazdy(
        Pojazd.objects.select_related(
            'konfiguracja__model__marka', 'konfiguracja__klasa_pojazdu', 'oddzial'
        ),
        user,
    )


def _parsuj_date(wartosc):
    if not wartosc:
        return None
    data = parse_datetime(wartosc)
    if data is None:
        try:
            data = datetime.datetime.combine(
                datetime.date.fromisoformat(wartosc), datetime.time.min
            )
        except ValueError:
            return None
    if timezone.is_naive(data):
        data = timezone.make_aware(data)
    return data


# ---------------------------------------------------------------- rezerwacje

def rezerwacje(request):
    lista = filtruj_rezerwacje(
        Rezerwacja.objects.select_related(
            'klient', 'uzytkownik_pojazdu', 'klasa_pojazdu', 'pojazd__konfiguracja__model__marka', 'cennik'
        ),
        request.user,
    )

    status = request.GET.get('status', '')
    szukaj = request.GET.get('szukaj', '')
    od = request.GET.get('od', '')
    do = request.GET.get('do', '')

    if status == 'aktywne':
        lista = lista.filter(status__in=Rezerwacja.STATUSY_BLOKUJACE)
    elif status:
        lista = lista.filter(status=status)
    if szukaj:
        lista = lista.filter(
            Q(numer__icontains=szukaj)
            | Q(klient__nazwa_firmy__icontains=szukaj)
            | Q(uzytkownik_pojazdu__nazwisko__icontains=szukaj)
            | Q(pojazd__numer_rejestracyjny__icontains=szukaj)
        )
    data_od = _parsuj_date(od)
    data_do = _parsuj_date(do)
    if data_od:
        lista = lista.filter(planowana_data_zwrotu__gte=data_od)
    if data_do:
        lista = lista.filter(planowana_data_wydania__lte=data_do)

    teraz = timezone.now()
    wszystkie = filtruj_rezerwacje(Rezerwacja.objects.all(), request.user)
    statystyki = {
        'aktywne': wszystkie.filter(status__in=Rezerwacja.STATUSY_BLOKUJACE).count(),
        'w_toku': wszystkie.filter(status='w_toku').count(),
        'do_wydania': wszystkie.filter(
            status__in=('nowa', 'potwierdzona'),
            planowana_data_wydania__range=(teraz, teraz + datetime.timedelta(days=7)),
        ).count(),
        'opoznione': wszystkie.filter(status='w_toku', planowana_data_zwrotu__lt=teraz).count(),
    }

    kontekst = {
        'rezerwacje': lista,
        'statusy': Rezerwacja.STATUS,
        'status': status,
        'szukaj': szukaj,
        'od': od,
        'do': do,
        'statystyki': statystyki,
    }
    template = 'wynajmy/rezerwacje_view.html' if request.headers.get('HX-Request') else 'wynajmy/rezerwacje.html'
    return render(request, template, kontekst)


def _formularz_rezerwacji(request, rezerwacja=None):
    """Wspolna obsluga dodawania i edycji rezerwacji."""
    if rezerwacja is not None and not widzi_rezerwacje(request.user, rezerwacja):
        raise Http404('Rezerwacja należy do innego oddziału.')
    if request.method == 'POST':
        form = RezerwacjaForm(request.POST, instance=rezerwacja, uzytkownik=request.user)
        formset = ZmianaPojazduFormSet(request.POST, instance=rezerwacja, form_kwargs={'uzytkownik': request.user})
        if form.is_valid() and formset.is_valid():
            obiekt = form.save()
            formset.instance = obiekt
            formset.save()
            messages.success(
                request,
                f'Zapisano rezerwację {obiekt.numer}.' if rezerwacja
                else f'Utworzono rezerwację {obiekt.numer}.'
            )
            return redirect('rezerwacja_szczegoly', pk=obiekt.pk)
    else:
        form = RezerwacjaForm(instance=rezerwacja, uzytkownik=request.user)
        formset = ZmianaPojazduFormSet(instance=rezerwacja, form_kwargs={'uzytkownik': request.user})

    return render(request, 'wynajmy/dodaj_rezerwacje.html', {
        'form': form,
        'formset': formset,
        'pojazdy': pojazdy_do_wyboru(request.user),
        'rezerwacja': rezerwacja,
        'tytul': f'Edytuj rezerwację {rezerwacja.numer}' if rezerwacja else 'Dodaj rezerwację',
        'przycisk': 'Zapisz zmiany' if rezerwacja else 'Zapisz',
    })


@wymaga(OPERACJE)
def dodaj_rezerwacje(request):
    return _formularz_rezerwacji(request)


@wymaga(OPERACJE)
def edytuj_rezerwacje(request, pk):
    return _formularz_rezerwacji(request, get_object_or_404(Rezerwacja, pk=pk))


def rezerwacja_szczegoly(request, pk):
    r = get_object_or_404(
        Rezerwacja.objects.select_related(
            'klient', 'uzytkownik_pojazdu', 'klasa_pojazdu',
            'pojazd__konfiguracja__model__marka', 'cennik',
        ),
        pk=pk,
    )
    if not widzi_rezerwacje(request.user, r):
        raise Http404('Rezerwacja należy do innego oddziału.')
    sekcje = [
        {'naglowek': 'Dane rezerwacji', 'pola': [
            ('Numer', r.numer),
            ('Status', r.get_status_display()),
            ('Typ', r.get_typ_display()),
            ('Klient', str(r.klient), f'/kontrahenci/{r.klient_id}/'),
            ('Użytkownik pojazdu', str(r.uzytkownik_pojazdu), f'/uzytkownicy-pojazdow/{r.uzytkownik_pojazdu_id}/'),
            ('MPK klienta', r.mpk_klienta),
            ('Data utworzenia', r.data_utworzenia),
        ]},
        {'naglowek': 'Pojazd i rozliczenie', 'pola': [
            ('Klasa pojazdu', str(r.klasa_pojazdu)),
            ('Pojazd', str(r.pojazd) if r.pojazd else None, f'/pojazdy/{r.pojazd_id}/' if r.pojazd_id else None),
            ('Cennik', str(r.cennik) if r.cennik else None, f'/cenniki/{r.cennik_id}/' if r.cennik_id else None),
            ('Cena jednostkowa', f'{r.cena_jednostkowa} {r.waluta}' if r.cena_jednostkowa is not None else None),
            ('Liczba dni', r.liczba_dni),
            ('Wartość całkowita', f'{r.wartosc_calkowita} {r.waluta}' if r.wartosc_calkowita is not None else None),
        ]},
        {'naglowek': 'Wydanie', 'pola': [
            ('Planowana data wydania', r.planowana_data_wydania),
            ('Faktyczna data wydania', r.faktyczna_data_wydania),
            ('Przebieg przy wydaniu', f'{r.przebieg_wydania} km' if r.przebieg_wydania is not None else None),
            ('Oddział wydania', r.oddzial_wydania),
            ('Podstawienie', tak_nie(r.podstawienie)),
            ('Adres podstawienia', r.adres_podstawienia),
        ]},
        {'naglowek': 'Zwrot', 'pola': [
            ('Planowana data zwrotu', r.planowana_data_zwrotu),
            ('Faktyczna data zwrotu', r.faktyczna_data_zwrotu),
            ('Przebieg przy zwrocie', f'{r.przebieg_zwrotu} km' if r.przebieg_zwrotu is not None else None),
            ('Przejechane kilometry', f'{r.przejechane_km} km' if r.przejechane_km is not None else None),
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

    akcje = []
    if r.status in ('nowa', 'potwierdzona'):
        akcje.append({'url': f'/rezerwacje/{r.pk}/wydanie/', 'label': 'Wydaj pojazd', 'klasa': 'btn-primary'})
    if r.status == 'w_toku':
        akcje.append({'url': f'/rezerwacje/{r.pk}/zwrot/', 'label': 'Przyjmij zwrot', 'klasa': 'btn-primary'})
    if r.status in Rezerwacja.STATUSY_BLOKUJACE:
        akcje.append({'url': f'/rezerwacje/{r.pk}/anuluj/', 'label': 'Anuluj rezerwację', 'klasa': 'btn-danger', 'post': True})

    return widok_szczegolow(
        request, f'Rezerwacja {r.numer}', sekcje,
        f'/rezerwacje/{pk}/edytuj/', '/rezerwacje/',
        akcje=akcje,
        usun_url=url_usuwania('rezerwacja', pk),
        uprawnienie_edycji=OPERACJE,
        odznaka={'tekst': r.get_status_display(), 'kolor': r.kolor_statusu},
        ostrzezenie='Termin zwrotu minął, a pojazd nie został zwrócony.' if r.czy_opozniona else None,
    )


@wymaga(OPERACJE)
def wydanie_rezerwacji(request, pk):
    r = get_object_or_404(Rezerwacja, pk=pk)
    if not widzi_rezerwacje(request.user, r):
        raise Http404('Rezerwacja należy do innego oddziału.')
    if r.status not in ('nowa', 'potwierdzona'):
        messages.error(request, f'Rezerwacji {r.numer} nie można wydać (status: {r.get_status_display()}).')
        return redirect('rezerwacja_szczegoly', pk=pk)

    if request.method == 'POST':
        form = WydanieForm(request.POST, instance=r, uzytkownik=request.user)
        if form.is_valid():
            obiekt = form.save(commit=False)
            obiekt.wydaj(obiekt.faktyczna_data_wydania, obiekt.przebieg_wydania)
            messages.success(request, f'Wydano pojazd {obiekt.pojazd} — rezerwacja {obiekt.numer} jest w toku.')
            return redirect('rezerwacja_szczegoly', pk=pk)
    else:
        form = WydanieForm(instance=r, uzytkownik=request.user)

    return render(request, 'wynajmy/protokol.html', {
        'form': form,
        'rezerwacja': r,
        'tytul': f'Wydanie pojazdu — {r.numer}',
        'opis': 'Potwierdź datę wydania i stan licznika. Rezerwacja przejdzie w status „W toku”, '
                'a pojazd zostanie oznaczony jako wynajęty.',
        'przycisk': 'Wydaj pojazd',
    })


@wymaga(OPERACJE)
def zwrot_rezerwacji(request, pk):
    r = get_object_or_404(Rezerwacja, pk=pk)
    if not widzi_rezerwacje(request.user, r):
        raise Http404('Rezerwacja należy do innego oddziału.')
    if r.status != 'w_toku':
        messages.error(request, f'Rezerwacja {r.numer} nie jest w toku — nie ma czego zwracać.')
        return redirect('rezerwacja_szczegoly', pk=pk)

    if request.method == 'POST':
        form = ZwrotForm(request.POST, instance=r)
        if form.is_valid():
            obiekt = form.save(commit=False)
            obiekt.zwroc(obiekt.faktyczna_data_zwrotu, obiekt.przebieg_zwrotu)
            messages.success(request, f'Przyjęto zwrot pojazdu — rezerwacja {obiekt.numer} zakończona.')
            return redirect('rezerwacja_szczegoly', pk=pk)
    else:
        form = ZwrotForm(instance=r)

    return render(request, 'wynajmy/protokol.html', {
        'form': form,
        'rezerwacja': r,
        'tytul': f'Zwrot pojazdu — {r.numer}',
        'opis': 'Potwierdź datę zwrotu i stan licznika. Rezerwacja zostanie zamknięta, '
                'a pojazd wróci do statusu „Dostępny”.',
        'przycisk': 'Przyjmij zwrot',
    })


@wymaga(OPERACJE)
def anuluj_rezerwacje(request, pk):
    r = get_object_or_404(Rezerwacja, pk=pk)
    if not widzi_rezerwacje(request.user, r):
        raise Http404('Rezerwacja należy do innego oddziału.')
    if request.method != 'POST':
        return redirect('rezerwacja_szczegoly', pk=pk)
    if r.status not in Rezerwacja.STATUSY_BLOKUJACE:
        messages.error(request, f'Rezerwacja {r.numer} jest już zamknięta.')
    else:
        r.anuluj()
        messages.success(request, f'Anulowano rezerwację {r.numer}.')
    return redirect('rezerwacja_szczegoly', pk=pk)


# ----------------------------------------------------------------- kalendarz

def kalendarz(request):
    """Oś czasu: pojazdy w wierszach, dni w kolumnach."""
    try:
        dni_zakres = max(7, min(60, int(request.GET.get('dni', 30))))
    except ValueError:
        dni_zakres = 30

    start_str = request.GET.get('start', '')
    try:
        start = datetime.date.fromisoformat(start_str) if start_str else timezone.localdate()
    except ValueError:
        start = timezone.localdate()
    koniec = start + datetime.timedelta(days=dni_zakres)

    okno_od = timezone.make_aware(datetime.datetime.combine(start, datetime.time.min))
    okno_do = timezone.make_aware(datetime.datetime.combine(koniec, datetime.time.min))

    lista = filtruj_rezerwacje(Rezerwacja.objects.all(), request.user).filter(
        status__in=Rezerwacja.STATUSY_BLOKUJACE,
        planowana_data_wydania__lt=okno_do,
        planowana_data_zwrotu__gt=okno_od,
        pojazd__isnull=False,
    ).select_related('klient', 'pojazd')

    wg_pojazdu = {}
    for r in lista:
        wg_pojazdu.setdefault(r.pojazd_id, []).append(r)

    dni = [start + datetime.timedelta(days=i) for i in range(dni_zakres)]
    wiersze = []
    for pojazd in pojazdy_do_wyboru(request.user).order_by('numer_rejestracyjny'):
        paski = []
        for r in wg_pojazdu.get(pojazd.id, []):
            od_dnia = max(0, (timezone.localtime(r.planowana_data_wydania).date() - start).days)
            do_dnia = min(dni_zakres, (timezone.localtime(r.planowana_data_zwrotu).date() - start).days + 1)
            if do_dnia <= od_dnia:
                do_dnia = od_dnia + 1
            paski.append({
                'rezerwacja': r,
                'start': od_dnia + 1,          # kolumny CSS grid licza sie od 1
                'koniec': do_dnia + 1,
                'kolor': r.kolor_statusu,
            })
        wiersze.append({'pojazd': pojazd, 'paski': paski})

    kontekst = {
        'dni': dni,
        'liczba_dni': dni_zakres,
        'wiersze': wiersze,
        'start': start,
        'dzis': timezone.localdate(),
        'poprzedni': (start - datetime.timedelta(days=dni_zakres)).isoformat(),
        'nastepny': (start + datetime.timedelta(days=dni_zakres)).isoformat(),
    }
    template = 'wynajmy/kalendarz_view.html' if request.headers.get('HX-Request') else 'wynajmy/kalendarz.html'
    return render(request, template, kontekst)


# ----------------------------------------------------------------------- API

def api_wycena(request):
    """Podpowiedź cennika i ceny dla klienta + klasy + terminu."""
    klasa = KlasaPojazdu.objects.filter(pk=request.GET.get('klasa') or 0).first()
    klient_id = request.GET.get('klient') or None
    cennik = None
    if request.GET.get('cennik'):
        cennik = Cennik.objects.filter(pk=request.GET['cennik']).first()
    if cennik is None:
        cennik = znajdz_cennik(klient_id and int(klient_id), klasa)

    cena = cennik.cena_dla_klasy(klasa) if cennik else None
    od = _parsuj_date(request.GET.get('od'))
    do = _parsuj_date(request.GET.get('do'))

    dni = 0
    if od and do and do > od:
        dni = max(1, -(-int((do - od).total_seconds()) // 86400))

    jednostki = dni
    if cennik and dni:
        if cennik.typ_stawki == 'tygodniowa':
            jednostki = max(1, -(-dni // 7))
        elif cennik.typ_stawki == 'miesieczna':
            jednostki = max(1, -(-dni // 30))

    wartosc = None
    if cena is not None and jednostki:
        wartosc = str((cena * Decimal(jednostki)).quantize(Decimal('0.01')))

    return JsonResponse({
        'cennik_id': cennik.pk if cennik else None,
        'cennik': str(cennik) if cennik else None,
        'typ_stawki': cennik.get_typ_stawki_display() if cennik else None,
        'waluta': cennik.waluta if cennik else None,
        'cena': str(cena) if cena is not None else None,
        'dni': dni,
        'jednostki': jednostki,
        'wartosc': wartosc,
    })


def api_dostepnosc(request):
    """Lista ID pojazdów zajętych w podanym terminie (do oznaczeń w modalu)."""
    od = _parsuj_date(request.GET.get('od'))
    do = _parsuj_date(request.GET.get('do'))
    pomin = request.GET.get('rezerwacja') or None

    if not od or not do or do <= od:
        return JsonResponse({'zajete': [], 'termin': False})

    zajete = Rezerwacja.objects.filter(
        status__in=Rezerwacja.STATUSY_BLOKUJACE,
        planowana_data_wydania__lt=do,
        planowana_data_zwrotu__gt=od,
    )
    if pomin:
        zajete = zajete.exclude(pk=pomin)

    wynik = {}
    for r in zajete.select_related('klient'):
        etykieta = f'{r.numer} · {r.klient}'
        for pojazd_id in [r.pojazd_id] + list(r.zmiany_pojazdu.values_list('pojazd_id', flat=True)):
            if pojazd_id:
                wynik.setdefault(str(pojazd_id), etykieta)

    return JsonResponse({'zajete': wynik, 'termin': True})


# ------------------------------------------------------------------- cenniki

def cenniki(request):
    lista = Cennik.objects.all().select_related('kontrahent').prefetch_related('pozycje')
    template = 'wynajmy/cenniki_view.html' if request.headers.get('HX-Request') else 'wynajmy/cenniki.html'
    return render(request, template, {'cenniki': lista})


@wymaga(SLOWNIKI)
def dodaj_cennik(request):
    if request.method == 'POST':
        form = CennikForm(request.POST)
        formset = PozycjaCennikaFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            cennik = form.save()
            formset.instance = cennik
            formset.save()
            messages.success(request, f'Dodano cennik „{cennik.nazwa}”.')
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
    return widok_szczegolow(request, f'Cennik: {c.nazwa}', sekcje, f'/cenniki/{pk}/edytuj/', '/cenniki/', usun_url=url_usuwania('cennik', pk), uprawnienie_edycji=SLOWNIKI)


@wymaga(SLOWNIKI)
def edytuj_cennik(request, pk):
    cennik = get_object_or_404(Cennik, pk=pk)
    if request.method == 'POST':
        form = CennikForm(request.POST, instance=cennik)
        formset = PozycjaCennikaFormSet(request.POST, instance=cennik)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f'Zapisano cennik „{cennik.nazwa}”.')
            return redirect('cenniki')
    else:
        form = CennikForm(instance=cennik)
        formset = PozycjaCennikaFormSet(instance=cennik)
    return render(request, 'wynajmy/dodaj_cennik.html', {
        'form': form, 'formset': formset,
        'tytul': f'Edytuj cennik: {cennik.nazwa}', 'przycisk': 'Zapisz zmiany',
    })
