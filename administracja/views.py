from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .forms import UzytkownikForm

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