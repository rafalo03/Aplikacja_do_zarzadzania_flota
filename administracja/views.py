import json

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .forms import UzytkownikForm
from .models import UkladTabeli

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
