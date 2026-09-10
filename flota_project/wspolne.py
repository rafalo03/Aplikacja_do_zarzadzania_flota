"""Widoki i pomocniki uzywane przez wszystkie aplikacje projektu."""

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import ProtectedError
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404

from administracja.uprawnienia import ADMINISTRACJA, USUWANIE, ma_uprawnienie, wymaga


def widok_szczegolow(request, tytul, sekcje, edytuj_url=None, powrot_url=None,
                     akcje=None, odznaka=None, ostrzezenie=None, usun_url=None,
                     uprawnienie_edycji=None):
    """Uniwersalny widok szczegolow.

    akcje              – dodatkowe przyciski: [{'url', 'label', 'klasa', 'post'}]
    odznaka            – status obok tytulu: {'tekst', 'kolor'}
    ostrzezenie        – komunikat nad trescia
    usun_url           – adres potwierdzenia usuniecia (czerwony przycisk „Usuń”)
    uprawnienie_edycji – uprawnienie wymagane do pokazania przycisku „Edytuj”

    Przyciski, na ktore uzytkownik nie ma uprawnien, po prostu znikaja — dostep
    i tak blokuja dekoratory na widokach docelowych.
    """
    if uprawnienie_edycji and not ma_uprawnienie(request.user, uprawnienie_edycji):
        edytuj_url = None
    if usun_url and not ma_uprawnienie(request.user, USUWANIE):
        usun_url = None

    template = 'szczegoly_view.html' if request.headers.get('HX-Request') else 'szczegoly.html'
    return render(request, template, {
        'tytul': tytul,
        'sekcje': sekcje,
        'edytuj_url': edytuj_url,
        'powrot_url': powrot_url,
        'akcje': akcje or [],
        'odznaka': odznaka,
        'ostrzezenie': ostrzezenie,
        'usun_url': usun_url,
    })


def tak_nie(wartosc):
    return 'Tak' if wartosc else 'Nie'


def url_usuwania(typ, pk):
    return f'/usun/{typ}/{pk}/'


def _rejestr():
    """Mapa typ -> konfiguracja usuwania. Importy w srodku, by uniknac cykli."""
    from django.contrib.auth.models import User
    from administracja.models import Oddzial
    from kontrahenci.models import Kontrahent, UzytkownikPojazdu
    from pojazdy.models import Pojazd, Polisa, Marka, ModelPojazdu, KlasaPojazdu, Konfiguracja
    from serwis.models import ZlecenieSerwisowe, SzkodaBladcharska, Uszkodzenie
    from wynajmy.models import Rezerwacja, Cennik

    return {
        'pojazd': (Pojazd, 'pojazd', '/pojazdy/'),
        'polisa': (Polisa, 'polisę', '/polisy/'),
        'marka': (Marka, 'markę', '/marki/'),
        'model': (ModelPojazdu, 'model pojazdu', '/modele/'),
        'klasa': (KlasaPojazdu, 'klasę pojazdu', '/klasy/'),
        'konfiguracja': (Konfiguracja, 'konfigurację', '/konfiguracje/'),
        'kontrahent': (Kontrahent, 'kontrahenta', '/kontrahenci/'),
        'uzytkownik-pojazdu': (UzytkownikPojazdu, 'użytkownika pojazdu', '/uzytkownicy-pojazdow/'),
        'rezerwacja': (Rezerwacja, 'rezerwację', '/rezerwacje/'),
        'cennik': (Cennik, 'cennik', '/cenniki/'),
        'zlecenie': (ZlecenieSerwisowe, 'zlecenie serwisowe', '/zlecenia/'),
        'szkoda': (SzkodaBladcharska, 'szkodę', '/szkody/'),
        'uszkodzenie': (Uszkodzenie, 'uszkodzenie', '/uszkodzenia/'),
        'oddzial': (Oddzial, 'oddział', '/oddzialy/', ADMINISTRACJA),
        'uzytkownik': (User, 'użytkownika', '/uzytkownicy/', ADMINISTRACJA),
    }


def _powiazania(obiekt):
    """Lista opisow rekordow, ktore znikna razem z obiektem."""
    opisy = []
    for relacja in obiekt._meta.related_objects:
        akcesor = relacja.get_accessor_name()
        powiazane = getattr(obiekt, akcesor, None)
        if powiazane is None:
            continue
        if relacja.one_to_one:
            opisy.append(str(relacja.related_model._meta.verbose_name))
            continue
        liczba = powiazane.count()
        if liczba:
            opisy.append(f'{relacja.related_model._meta.verbose_name_plural}: {liczba}')
    return opisy


def usun_obiekt(request, typ, pk):
    """Usuwa rekord po potwierdzeniu. GET pokazuje ekran potwierdzenia."""
    wpis = _rejestr().get(typ)
    if wpis is None:
        raise Http404(f'Nieznany typ obiektu: {typ}')
    model, nazwa, powrot = wpis[:3]
    # rekordy administracyjne (konta, oddzialy) wymagaja szerszego uprawnienia
    uprawnienie = wpis[3] if len(wpis) > 3 else USUWANIE
    if not ma_uprawnienie(request.user, uprawnienie):
        raise PermissionDenied(f'Twoja rola nie pozwala na usunięcie tego rekordu ({nazwa}).')
    obiekt = get_object_or_404(model, pk=pk)
    szczegoly = f'{powrot}{pk}/'

    if typ == 'uzytkownik' and obiekt.pk == request.user.pk:
        messages.error(request, 'Nie możesz usunąć własnego konta.')
        return redirect(szczegoly)

    if request.method == 'POST':
        etykieta = str(obiekt)
        try:
            obiekt.delete()
        except ProtectedError as e:
            blokujace = {
                str(o._meta.verbose_name_plural) for o in e.protected_objects
            }
            messages.error(
                request,
                f'Nie można usunąć — rekord jest powiązany z: {", ".join(sorted(blokujace))}. '
                'Najpierw usuń lub przepnij powiązane rekordy.'
            )
            return redirect(szczegoly)
        messages.success(request, f'Usunięto {nazwa}: {etykieta}.')
        return redirect(powrot)

    return render(request, 'usun.html', {
        'obiekt': obiekt,
        'nazwa': nazwa,
        'powiazania': _powiazania(obiekt),
        'powrot_url': szczegoly,
        'akcja_url': url_usuwania(typ, pk),
    })
