import json

from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .forms import PojazdForm, PolisaForm, MarkaForm, ModelPojazduForm, KlasaPojazduForm, KonfiguracjaForm
from .models import Pojazd, Polisa, Marka, ModelPojazdu, KlasaPojazdu, Konfiguracja
from flota_project.wspolne import widok_szczegolow, tak_nie, url_usuwania
from administracja.uprawnienia import (
    FLOTA, SLOWNIKI, wymaga, filtruj_pojazdy, filtruj_po_pojezdzie, widzi_pojazd,
)

def pojazdy(request):
    pojazdy = filtruj_pojazdy(
        Pojazd.objects.select_related('konfiguracja__model__marka', 'oddzial'), request.user
    )

    szukaj = request.GET.get('szukaj', '')
    status = request.GET.get('status', '')
    stan = request.GET.get('stan', '')

    if szukaj:
        pojazdy = pojazdy.filter(numer_rejestracyjny__icontains=szukaj) | \
                  pojazdy.filter(konfiguracja__model__marka__nazwa__icontains=szukaj) | \
                  pojazdy.filter(konfiguracja__model__nazwa__icontains=szukaj)
    if status:
        pojazdy = pojazdy.filter(status=status)
    if stan:
        pojazdy = pojazdy.filter(stan=stan)

    template = 'pojazdy/pojazdy_view.html' if request.headers.get('HX-Request') else 'pojazdy/pojazdy.html' if request.headers.get('HX-Request') else 'pojazdy/pojazdy.html'

    return render(request, template, {
        'pojazdy': pojazdy,
        'szukaj': szukaj,
        'status': status,
        'stan': stan,
    })

@wymaga(FLOTA)
def dodaj_pojazd(request):
    if request.method == 'POST':
        form = PojazdForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('pojazdy')
    else:
        initial = {}
        wzor = None
        podobny = request.GET.get('podobny')
        if podobny:
            wzor = Pojazd.objects.filter(pk=podobny).first()
        if wzor:
            initial = {
                'konfiguracja': wzor.konfiguracja_id,
                'rok_produkcji': wzor.rok_produkcji,
                'data_zakupu': wzor.data_zakupu,
                'status': wzor.status,
                'stan': wzor.stan,
                'oddzial': wzor.oddzial_id,
                'dostawca': wzor.dostawca_id,
                'wlasciciel': wzor.wlasciciel_id,
                'wspolwlasciciel': wzor.wspolwlasciciel_id,
            }
        form = PojazdForm(initial=initial)
    konfiguracje = Konfiguracja.objects.select_related('model__marka', 'klasa_pojazdu')
    return render(request, 'pojazdy/dodaj_pojazd.html', {'form': form, 'konfiguracje': konfiguracje})

def pojazd_szczegoly(request, pk):
    pojazd = get_object_or_404(
        Pojazd.objects.select_related(
            'konfiguracja__model__marka', 'konfiguracja__klasa_pojazdu',
            'dostawca', 'wlasciciel', 'wspolwlasciciel'
        ),
        pk=pk,
    )
    if not widzi_pojazd(request.user, pojazd):
        raise Http404('Pojazd należy do innego oddziału.')
    template = 'pojazdy/pojazd_szczegoly_view.html' if request.headers.get('HX-Request') else 'pojazdy/pojazd_szczegoly.html'
    return render(request, template, {
        'pojazd': pojazd,
        'polisy': pojazd.polisy.all(),
        'rezerwacje': pojazd.rezerwacje.select_related('klient', 'uzytkownik_pojazdu')[:10],
        'zlecenia': pojazd.zlecenia_serwisowe.select_related('warsztat')[:10],
        'szkody': pojazd.szkody.select_related('warsztat')[:10],
        'uszkodzenia': pojazd.uszkodzenia.all()[:10],
    })

@wymaga(FLOTA)
def edytuj_pojazd(request, pk):
    pojazd = get_object_or_404(Pojazd, pk=pk)
    if not widzi_pojazd(request.user, pojazd):
        raise Http404('Pojazd należy do innego oddziału.')
    if request.method == 'POST':
        form = PojazdForm(request.POST, instance=pojazd)
        if form.is_valid():
            form.save()
            return redirect('pojazdy')
    else:
        form = PojazdForm(instance=pojazd)
    konfiguracje = Konfiguracja.objects.select_related('model__marka', 'klasa_pojazdu')
    return render(request, 'pojazdy/edytuj_pojazd.html', {'form': form, 'pojazd': pojazd, 'konfiguracje': konfiguracje})

@wymaga(FLOTA)
def zmien_stan_pojazdu(request, pk):
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=405)
    pojazd = get_object_or_404(Pojazd, pk=pk)
    if not widzi_pojazd(request.user, pojazd):
        return JsonResponse({'ok': False, 'blad': 'Brak dostępu do pojazdu'}, status=404)
    try:
        dane = json.loads(request.body)
    except (ValueError, TypeError):
        return JsonResponse({'ok': False}, status=400)
    stan = dane.get('stan')
    if stan not in dict(Pojazd.STAN):
        return JsonResponse({'ok': False, 'blad': 'Nieprawidłowy stan'}, status=400)
    pojazd.stan = stan
    pojazd.save()
    return JsonResponse({'ok': True})

def polisy(request):
    polisy = filtruj_po_pojezdzie(
        Polisa.objects.select_related('pojazd__konfiguracja__model__marka'), request.user
    )
    template = 'pojazdy/polisy_view.html' if request.headers.get('HX-Request') else 'pojazdy/polisy.html'
    return render(request, template, {'polisy': polisy})

@wymaga(FLOTA)
def dodaj_polise(request):
    if request.method == 'POST':
        form = PolisaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('polisy')
    else:
        form = PolisaForm()
    return render(request, 'pojazdy/dodaj_polise.html', {'form': form})

def marki(request):
    marki = Marka.objects.all()
    template = 'pojazdy/marki_view.html' if request.headers.get('HX-Request') else 'pojazdy/marki.html'
    return render(request, template, {'marki': marki})

@wymaga(SLOWNIKI)
def dodaj_marke(request):
    if request.method == 'POST':
        form = MarkaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('marki')
    else:
        form = MarkaForm()
    return render(request, 'pojazdy/dodaj_marke.html', {'form': form})

def modele(request):
    modele = ModelPojazdu.objects.all().select_related('marka')
    template = 'pojazdy/modele_view.html' if request.headers.get('HX-Request') else 'pojazdy/modele.html'
    return render(request, template, {'modele': modele})

@wymaga(SLOWNIKI)
def dodaj_model(request):
    if request.method == 'POST':
        form = ModelPojazduForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('modele')
    else:
        form = ModelPojazduForm()
    return render(request, 'pojazdy/dodaj_model.html', {'form': form})

def klasy(request):
    klasy = KlasaPojazdu.objects.all()
    template = 'pojazdy/klasy_view.html' if request.headers.get('HX-Request') else 'pojazdy/klasy.html'
    return render(request, template, {'klasy': klasy})

@wymaga(SLOWNIKI)
def dodaj_klase(request):
    if request.method == 'POST':
        form = KlasaPojazduForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('klasy')
    else:
        form = KlasaPojazduForm()
    return render(request, 'pojazdy/dodaj_klase.html', {'form': form})

def konfiguracje(request):
    konfiguracje = Konfiguracja.objects.select_related('model__marka', 'klasa_pojazdu')
    template = 'pojazdy/konfiguracje_view.html' if request.headers.get('HX-Request') else 'pojazdy/konfiguracje.html'
    return render(request, template, {'konfiguracje': konfiguracje})

@wymaga(SLOWNIKI)
def dodaj_konfiguracje(request):
    if request.method == 'POST':
        form = KonfiguracjaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('konfiguracje')
    else:
        form = KonfiguracjaForm()
    return render(request, 'pojazdy/dodaj_konfiguracje.html', {'form': form})

@wymaga(SLOWNIKI)
def edytuj_konfiguracje(request, pk):
    konfiguracja = get_object_or_404(Konfiguracja, pk=pk)
    if request.method == 'POST':
        form = KonfiguracjaForm(request.POST, instance=konfiguracja)
        if form.is_valid():
            form.save()
            return redirect('konfiguracje')
    else:
        form = KonfiguracjaForm(instance=konfiguracja)
    return render(request, 'pojazdy/edytuj_konfiguracje.html', {'form': form, 'konfiguracja': konfiguracja})

def marka_szczegoly(request, pk):
    marka = get_object_or_404(Marka, pk=pk)
    modele_marki = ', '.join(m.nazwa for m in marka.modele.all())
    sekcje = [{'naglowek': 'Dane marki', 'pola': [
        ('Nazwa', marka.nazwa),
        ('Liczba modeli', marka.modele.count()),
        ('Modele', modele_marki),
    ]}]
    return widok_szczegolow(request, f'Marka — {marka.nazwa}', sekcje, f'/marki/{pk}/edytuj/', '/marki/', usun_url=url_usuwania('marka', pk), uprawnienie_edycji=SLOWNIKI)

@wymaga(SLOWNIKI)
def edytuj_marke(request, pk):
    marka = get_object_or_404(Marka, pk=pk)
    if request.method == 'POST':
        form = MarkaForm(request.POST, instance=marka)
        if form.is_valid():
            form.save()
            return redirect('marki')
    else:
        form = MarkaForm(instance=marka)
    return render(request, 'pojazdy/dodaj_marke.html', {'form': form, 'tytul': f'Edytuj markę — {marka.nazwa}', 'przycisk': 'Zapisz zmiany'})

def model_szczegoly(request, pk):
    model = get_object_or_404(ModelPojazdu.objects.select_related('marka'), pk=pk)
    sekcje = [{'naglowek': 'Dane modelu', 'pola': [
        ('Marka', model.marka.nazwa),
        ('Model', model.nazwa),
        ('Liczba konfiguracji', model.konfiguracje.count()),
    ]}]
    return widok_szczegolow(request, f'Model — {model}', sekcje, f'/modele/{pk}/edytuj/', '/modele/', usun_url=url_usuwania('model', pk), uprawnienie_edycji=SLOWNIKI)

@wymaga(SLOWNIKI)
def edytuj_model(request, pk):
    model = get_object_or_404(ModelPojazdu, pk=pk)
    if request.method == 'POST':
        form = ModelPojazduForm(request.POST, instance=model)
        if form.is_valid():
            form.save()
            return redirect('modele')
    else:
        form = ModelPojazduForm(instance=model)
    return render(request, 'pojazdy/dodaj_model.html', {'form': form, 'tytul': f'Edytuj model — {model}', 'przycisk': 'Zapisz zmiany'})

def klasa_szczegoly(request, pk):
    klasa = get_object_or_404(KlasaPojazdu, pk=pk)
    sekcje = [{'naglowek': 'Dane klasy', 'pola': [
        ('Nazwa', klasa.nazwa),
        ('Opis', klasa.opis),
        ('Liczba konfiguracji', klasa.konfiguracja_set.count()),
    ]}]
    return widok_szczegolow(request, f'Klasa — {klasa.nazwa}', sekcje, f'/klasy/{pk}/edytuj/', '/klasy/', usun_url=url_usuwania('klasa', pk), uprawnienie_edycji=SLOWNIKI)

@wymaga(SLOWNIKI)
def edytuj_klase(request, pk):
    klasa = get_object_or_404(KlasaPojazdu, pk=pk)
    if request.method == 'POST':
        form = KlasaPojazduForm(request.POST, instance=klasa)
        if form.is_valid():
            form.save()
            return redirect('klasy')
    else:
        form = KlasaPojazduForm(instance=klasa)
    return render(request, 'pojazdy/dodaj_klase.html', {'form': form, 'tytul': f'Edytuj klasę — {klasa.nazwa}', 'przycisk': 'Zapisz zmiany'})

def konfiguracja_szczegoly(request, pk):
    k = get_object_or_404(Konfiguracja.objects.select_related('model__marka', 'klasa_pojazdu'), pk=pk)
    sekcje = [
        {'naglowek': 'Model i nadwozie', 'pola': [
            ('Marka', k.model.marka.nazwa),
            ('Model', k.model.nazwa),
            ('Wersja wyposażenia', k.wersja_wyposazenia),
            ('Typ nadwozia', k.get_typ_nadwozia_display()),
            ('Klasa pojazdu', k.klasa_pojazdu),
            ('Liczba drzwi', k.liczba_drzwi),
            ('Liczba pasażerów', k.maksymalna_liczba_pasazerow),
        ]},
        {'naglowek': 'Silnik i napęd', 'pola': [
            ('Pojemność silnika', k.pojemnosc_silnika),
            ('Rodzaj paliwa', k.get_rodzaj_paliwa_display()),
            ('Moc', f'{k.moc_km} KM ({k.moc_kw} kW)'),
            ('Skrzynia biegów', k.get_typ_skrzyni_display()),
            ('Napęd', k.get_naped_display()),
        ]},
        {'naglowek': 'Zużycie i serwis', 'pola': [
            ('Pojemność baku', f'{k.pojemnosc_baku} l' if k.pojemnosc_baku else None),
            ('Spalanie', f'{k.spalanie_l100km} l/100km' if k.spalanie_l100km else None),
            ('Emisja CO2', f'{k.co2_gkm} g/km' if k.co2_gkm else None),
            ('Interwał przeglądu', f'{k.interwał_przeglądu_km} km / {k.interwał_przeglądu_miesięcy} mies.'),
            ('Liczba pojazdów', k.pojazdy.count()),
        ]},
    ]
    return widok_szczegolow(request, f'Konfiguracja — {k}', sekcje, f'/konfiguracje/{pk}/edytuj/', '/konfiguracje/', usun_url=url_usuwania('konfiguracja', pk), uprawnienie_edycji=SLOWNIKI)

def polisa_szczegoly(request, pk):
    polisa = get_object_or_404(Polisa.objects.select_related('pojazd__konfiguracja__model__marka'), pk=pk)
    if not widzi_pojazd(request.user, polisa.pojazd):
        raise Http404('Polisa dotyczy pojazdu z innego oddziału.')
    zakres = ', '.join(n for n, w in [('OC', polisa.rodzaj_oc), ('AC', polisa.rodzaj_ac), ('NNW', polisa.rodzaj_nnw), ('Assistance', polisa.rodzaj_assistance)] if w)
    sekcje = [{'naglowek': 'Dane polisy', 'pola': [
        ('Pojazd', str(polisa.pojazd), f'/pojazdy/{polisa.pojazd_id}/'),
        ('Numer polisy', polisa.numer_polisy),
        ('Umowa generalna', polisa.numer_umowy_generalnej),
        ('Ubezpieczyciel', polisa.ubezpieczyciel),
        ('Zakres', zakres),
        ('Data od', polisa.data_od),
        ('Data do', polisa.data_do),
        ('Skan', 'Pobierz' if polisa.skan else None, polisa.skan.url if polisa.skan else None),
        ('Uwagi', polisa.uwagi),
    ]}]
    return widok_szczegolow(request, f'Polisa — {polisa.numer_polisy}', sekcje, f'/polisy/{pk}/edytuj/', '/polisy/', usun_url=url_usuwania('polisa', pk), uprawnienie_edycji=FLOTA)

@wymaga(FLOTA)
def edytuj_polise(request, pk):
    polisa = get_object_or_404(Polisa, pk=pk)
    if not widzi_pojazd(request.user, polisa.pojazd):
        raise Http404('Polisa dotyczy pojazdu z innego oddziału.')
    if request.method == 'POST':
        form = PolisaForm(request.POST, request.FILES, instance=polisa)
        if form.is_valid():
            form.save()
            return redirect('polisy')
    else:
        form = PolisaForm(instance=polisa)
    return render(request, 'pojazdy/dodaj_polise.html', {'form': form, 'tytul': f'Edytuj polisę — {polisa.numer_polisy}', 'przycisk': 'Zapisz zmiany'})
