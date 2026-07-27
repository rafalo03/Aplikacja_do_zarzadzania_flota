from django.shortcuts import render, redirect, get_object_or_404
from .models import ZlecenieSerwisowe, SzkodaBladcharska, Uszkodzenie
from .forms import ZlecenieSerwisoweForms, SzkodaBlacharskaForm, UszkodzenieForm

def zlecenia(request):
    zlecenia = ZlecenieSerwisowe.objects.all().select_related('pojazd', 'warsztat')
    template = 'serwis/zlecenia_view.html' if request.headers.get('HX-Request') else 'serwis/zlecenia.html'
    return render(request, template, {'zlecenia': zlecenia})

def dodaj_zlecenie(request):
    if request.method == 'POST':
        form = ZlecenieSerwisoweForms(request.POST)
        if form.is_valid():
            form.save()
            return redirect('zlecenia')
    else:
        form = ZlecenieSerwisoweForms()
    return render(request, 'serwis/dodaj_zlecenie.html', {'form': form})

def szkody(request):
    szkody = SzkodaBladcharska.objects.all().select_related('pojazd', 'warsztat')
    template = 'serwis/szkody_view.html' if request.headers.get('HX-Request') else 'serwis/szkody.html'
    return render(request, template, {'szkody': szkody})

def dodaj_szkode(request):
    if request.method == 'POST':
        form = SzkodaBlacharskaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('szkody')
    else:
        form = SzkodaBlacharskaForm()
    return render(request, 'serwis/dodaj_szkode.html', {'form': form})

def uszkodzenia(request):
    uszkodzenia = Uszkodzenie.objects.all().select_related('pojazd')
    template = 'serwis/uszkodzenia_view.html' if request.headers.get('HX-Request') else 'serwis/uszkodzenia.html'
    return render(request, template, {'uszkodzenia': uszkodzenia})
def dodaj_uszkodzenie(request):
    if request.method == 'POST':
        form = UszkodzenieForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('uszkodzenia')
    else:
        form = UszkodzenieForm()
    return render(request, 'serwis/dodaj_uszkodzenie.html', {'form': form})

def widok_szczegolow(request, tytul, sekcje, edytuj_url=None, powrot_url=None):
    template = 'szczegoly_view.html' if request.headers.get('HX-Request') else 'szczegoly.html'
    return render(request, template, {'tytul': tytul, 'sekcje': sekcje, 'edytuj_url': edytuj_url, 'powrot_url': powrot_url})

def tak_nie(wartosc):
    return 'Tak' if wartosc else 'Nie'

def zlecenie_szczegoly(request, pk):
    z = get_object_or_404(ZlecenieSerwisowe.objects.select_related('pojazd', 'najemca', 'warsztat'), pk=pk)
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
    return widok_szczegolow(request, f'Zlecenie serwisowe #{z.pk}', sekcje, f'/zlecenia/{pk}/edytuj/', '/zlecenia/')

def edytuj_zlecenie(request, pk):
    zlecenie = get_object_or_404(ZlecenieSerwisowe, pk=pk)
    if request.method == 'POST':
        form = ZlecenieSerwisoweForms(request.POST, instance=zlecenie)
        if form.is_valid():
            form.save()
            return redirect('zlecenia')
    else:
        form = ZlecenieSerwisoweForms(instance=zlecenie)
    return render(request, 'serwis/dodaj_zlecenie.html', {'form': form, 'tytul': f'Edytuj zlecenie #{zlecenie.pk}', 'przycisk': 'Zapisz zmiany'})

def szkoda_szczegoly(request, pk):
    s = get_object_or_404(SzkodaBladcharska.objects.select_related('pojazd', 'najemca', 'warsztat'), pk=pk)
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
    return widok_szczegolow(request, f'Szkoda blacharska #{s.pk}', sekcje, f'/szkody/{pk}/edytuj/', '/szkody/')

def edytuj_szkode(request, pk):
    szkoda = get_object_or_404(SzkodaBladcharska, pk=pk)
    if request.method == 'POST':
        form = SzkodaBlacharskaForm(request.POST, instance=szkoda)
        if form.is_valid():
            form.save()
            return redirect('szkody')
    else:
        form = SzkodaBlacharskaForm(instance=szkoda)
    return render(request, 'serwis/dodaj_szkode.html', {'form': form, 'tytul': f'Edytuj szkodę #{szkoda.pk}', 'przycisk': 'Zapisz zmiany'})

def uszkodzenie_szczegoly(request, pk):
    u = get_object_or_404(Uszkodzenie.objects.select_related('pojazd'), pk=pk)
    sekcje = [{'naglowek': 'Dane uszkodzenia', 'pola': [
        ('Pojazd', str(u.pojazd), f'/pojazdy/{u.pojazd_id}/'),
        ('Data wykrycia', u.data_wykrycia),
        ('Zgłaszający', u.zglaszajacy),
        ('Naprawione', tak_nie(u.naprawione)),
        ('Koszt naprawy', u.koszt_naprawy),
        ('Zdjęcie', 'Zobacz' if u.zdjecie else None, u.zdjecie.url if u.zdjecie else None),
        ('Opis', u.opis),
    ]}]
    return widok_szczegolow(request, f'Uszkodzenie #{u.pk}', sekcje, f'/uszkodzenia/{pk}/edytuj/', '/uszkodzenia/')

def edytuj_uszkodzenie(request, pk):
    uszkodzenie = get_object_or_404(Uszkodzenie, pk=pk)
    if request.method == 'POST':
        form = UszkodzenieForm(request.POST, request.FILES, instance=uszkodzenie)
        if form.is_valid():
            form.save()
            return redirect('uszkodzenia')
    else:
        form = UszkodzenieForm(instance=uszkodzenie)
    return render(request, 'serwis/dodaj_uszkodzenie.html', {'form': form, 'tytul': f'Edytuj uszkodzenie #{uszkodzenie.pk}', 'przycisk': 'Zapisz zmiany'})
