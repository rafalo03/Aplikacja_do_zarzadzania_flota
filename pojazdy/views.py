from django.shortcuts import render, redirect
from .models import Pojazd
from .forms import PojazdForm, PolisaForm, MarkaForm, ModelPojazduForm, KlasaPojazduForm
from .models import Pojazd, Polisa, Marka, ModelPojazdu, KlasaPojazdu

def pojazdy(request):
    pojazdy = Pojazd.objects.all().select_related('konfiguracja__model__marka')

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

def dodaj_pojazd(request):
    if request.method == 'POST':
        form = PojazdForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('pojazdy')
    else:
        form = PojazdForm()
    return render(request, 'pojazdy/dodaj_pojazd.html', {'form': form})

def polisy(request):
    polisy = Polisa.objects.all().select_related('pojazd__konfiguracja__model__marka')
    template = 'pojazdy/polisy_view.html' if request.headers.get('HX-Request') else 'pojazdy/polisy.html'
    return render(request, template, {'polisy': polisy})

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

def dodaj_klase(request):
    if request.method == 'POST':
        form = KlasaPojazduForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('klasy')
    else:
        form = KlasaPojazduForm()
    return render(request, 'pojazdy/dodaj_klase.html', {'form': form})