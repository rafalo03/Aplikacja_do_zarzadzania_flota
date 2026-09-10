"""Role uzytkownikow, uprawnienia i ograniczenie danych do oddzialu.

Cztery role (patrz ProfilUzytkownika.ROLE) maja z gory ustalone zestawy
uprawnien. Uprawnienie to jedno z:

  podglad       – odczyt list i kart (kazda rola)
  operacje      – dodawanie i edycja rezerwacji, serwisu, kontrahentow
  flota         – dodawanie i edycja pojazdow oraz polis
  slowniki      – marki, modele, klasy, konfiguracje, cenniki
  usuwanie      – kasowanie rekordow
  administracja – uzytkownicy i oddzialy

Widocznosc danych jest dodatkowo zawezana do oddzialu uzytkownika; role
administrator i kierownik widza cala flote, tak samo konto bez wskazanego
oddzialu.
"""

from functools import wraps

from django.core.exceptions import PermissionDenied
from django.db.models import Q

PODGLAD = 'podglad'
OPERACJE = 'operacje'
FLOTA = 'flota'
SLOWNIKI = 'slowniki'
USUWANIE = 'usuwanie'
ADMINISTRACJA = 'administracja'

UPRAWNIENIA_ROL = {
    'administrator': {PODGLAD, OPERACJE, FLOTA, SLOWNIKI, USUWANIE, ADMINISTRACJA},
    'kierownik': {PODGLAD, OPERACJE, FLOTA, SLOWNIKI, USUWANIE},
    'pracownik': {PODGLAD, OPERACJE},
    'podglad': {PODGLAD},
}

# Role widzace dane wszystkich oddzialow
ROLE_BEZ_OGRANICZEN = ('administrator', 'kierownik')

OPISY_UPRAWNIEN = {
    OPERACJE: 'prowadzenia rezerwacji, serwisu i kontrahentów',
    FLOTA: 'zarządzania pojazdami i polisami',
    SLOWNIKI: 'edycji słowników i cenników',
    USUWANIE: 'usuwania rekordów',
    ADMINISTRACJA: 'administracji systemem',
}


def profil(user):
    """Profil uzytkownika albo None (konta bez profilu traktujemy jak podglad)."""
    if not user or not user.is_authenticated:
        return None
    return getattr(user, 'profil', None)


def rola(user):
    """Rola uzytkownika. Superuser Django jest zawsze administratorem."""
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return 'administrator'
    p = profil(user)
    return p.rola if p else 'podglad'


def ma_uprawnienie(user, uprawnienie):
    return uprawnienie in UPRAWNIENIA_ROL.get(rola(user), set())


def uprawnienia_uzytkownika(user):
    """Slownik dla szablonow: {{ uprawnienia.usuwanie }} itp."""
    dostepne = UPRAWNIENIA_ROL.get(rola(user), set())
    wynik = {nazwa: nazwa in dostepne for nazwa in
             (PODGLAD, OPERACJE, FLOTA, SLOWNIKI, USUWANIE, ADMINISTRACJA)}
    wynik['rola'] = rola(user)
    p = profil(user)
    wynik['oddzial'] = p.oddzial if p else None
    return wynik


def kontekst_uprawnien(request):
    """Context processor — udostepnia `uprawnienia` w kazdym szablonie."""
    return {'uprawnienia': uprawnienia_uzytkownika(getattr(request, 'user', None))}


def wymaga(uprawnienie):
    """Dekorator widoku: blokuje uzytkownikow bez wskazanego uprawnienia."""
    def dekorator(widok):
        @wraps(widok)
        def opakowany(request, *args, **kwargs):
            if not ma_uprawnienie(request.user, uprawnienie):
                opis = OPISY_UPRAWNIEN.get(uprawnienie, uprawnienie)
                raise PermissionDenied(f'Twoja rola nie pozwala na {opis}.')
            return widok(request, *args, **kwargs)
        return opakowany
    return dekorator


# ---------------------------------------------------------------- oddzialy

def oddzial_uzytkownika(user):
    """Oddzial ograniczajacy widocznosc danych albo None (brak ograniczen)."""
    if not user or not user.is_authenticated or user.is_superuser:
        return None
    if rola(user) in ROLE_BEZ_OGRANICZEN:
        return None
    p = profil(user)
    return p.oddzial if p else None


def filtruj_pojazdy(qs, user):
    oddzial = oddzial_uzytkownika(user)
    return qs if oddzial is None else qs.filter(oddzial=oddzial)


def filtruj_po_pojezdzie(qs, user, pole='pojazd__oddzial'):
    """Zaweza liste rekordow powiazanych z pojazdem do oddzialu uzytkownika."""
    oddzial = oddzial_uzytkownika(user)
    return qs if oddzial is None else qs.filter(**{pole: oddzial})


def filtruj_rezerwacje(qs, user):
    """Rezerwacje oddzialu: wg pojazdu, a gdy pojazdu brak — wg oddzialu wydania."""
    oddzial = oddzial_uzytkownika(user)
    if oddzial is None:
        return qs
    return qs.filter(
        Q(pojazd__oddzial=oddzial)
        | Q(pojazd__isnull=True, oddzial_wydania=oddzial.nazwa)
    )


class WyborPojazduZOddzialu:
    """Mixin formularza: zawęża pole `pojazd` do oddziału użytkownika.

    Bez tego lista <select> zawierałaby auta z innych oddziałów i dałoby się je
    podstawić w POST, omijając filtrowanie list.
    """

    def __init__(self, *args, uzytkownik=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.uzytkownik = uzytkownik
        if uzytkownik is None or 'pojazd' not in self.fields:
            return
        from pojazdy.models import Pojazd  # import lokalny — unika cyklu
        self.fields['pojazd'].queryset = filtruj_pojazdy(
            Pojazd.objects.select_related('konfiguracja__model__marka'), uzytkownik
        )


def widzi_pojazd(user, pojazd):
    oddzial = oddzial_uzytkownika(user)
    return oddzial is None or (pojazd is not None and pojazd.oddzial_id == oddzial.pk)


def widzi_rezerwacje(user, rezerwacja):
    oddzial = oddzial_uzytkownika(user)
    if oddzial is None:
        return True
    if rezerwacja.pojazd_id:
        return rezerwacja.pojazd.oddzial_id == oddzial.pk
    return rezerwacja.oddzial_wydania == oddzial.nazwa
