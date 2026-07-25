from django.shortcuts import render, redirect
from .models import ZlecenieSerwisowe, SzkodaBladcharska, Uszkodzenie
from .forms import ZlecenieSerwisoweForms, SzkodaBlacharskaForm

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