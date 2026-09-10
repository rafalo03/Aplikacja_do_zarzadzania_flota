import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from kontrahenci.models import Kontrahent, UzytkownikPojazdu
from pojazdy.models import Marka, ModelPojazdu, KlasaPojazdu, Konfiguracja, Pojazd
from serwis.models import ZlecenieSerwisowe
from wynajmy.models import Rezerwacja

from .models import Oddzial, ProfilUzytkownika
from .uprawnienia import (
    ADMINISTRACJA, FLOTA, OPERACJE, SLOWNIKI, USUWANIE,
    ma_uprawnienie, oddzial_uzytkownika, rola, uprawnienia_uzytkownika,
)


def utworz_uzytkownika(login, rola='pracownik', oddzial=None, haslo='tajne123', profil=True):
    user = User.objects.create_user(login, password=haslo)
    if profil:
        ProfilUzytkownika.objects.create(user=user, rola=rola, oddzial=oddzial)
    return user


class BazaTestowa(TestCase):
    """Dwa oddzialy, po jednym pojezdzie i rezerwacji w kazdym."""

    def setUp(self):
        self.teraz = timezone.now().replace(microsecond=0)
        self.warszawa = Oddzial.objects.create(nazwa='Warszawa')
        self.krakow = Oddzial.objects.create(nazwa='Kraków')

        marka = Marka.objects.create(nazwa='Skoda')
        model = ModelPojazdu.objects.create(marka=marka, nazwa='Octavia')
        self.klasa = KlasaPojazdu.objects.create(nazwa='C')
        self.konfiguracja = Konfiguracja.objects.create(
            model=model, wersja_wyposazenia='Style', typ_nadwozia='kombi',
            klasa_pojazdu=self.klasa, pojemnosc_silnika='1.5', moc_km=150,
            rodzaj_paliwa='benzyna', typ_skrzyni='manualna', naped='fwd',
        )
        self.auto_wwa = self._pojazd('WX1000A', self.warszawa)
        self.auto_krk = self._pojazd('KR2000B', self.krakow)

        self.klient = Kontrahent.objects.create(nazwa_firmy='Klient sp. z o.o.', typ_klient=True)
        self.kierowca = UzytkownikPojazdu.objects.create(imie='Anna', nazwisko='Nowak')
        self.rez_wwa = self._rezerwacja(self.auto_wwa)
        self.rez_krk = self._rezerwacja(self.auto_krk)

    def _pojazd(self, rejestracja, oddzial):
        return Pojazd.objects.create(
            konfiguracja=self.konfiguracja, numer_rejestracyjny=rejestracja,
            rok_produkcji=2023, data_zakupu=self.teraz.date(), przebieg_km=10000,
            oddzial=oddzial,
        )

    def _rezerwacja(self, pojazd):
        return Rezerwacja.objects.create(
            typ='corpo', klient=self.klient, uzytkownik_pojazdu=self.kierowca,
            klasa_pojazdu=self.klasa, pojazd=pojazd,
            planowana_data_wydania=self.teraz,
            planowana_data_zwrotu=self.teraz + datetime.timedelta(days=3),
        )


class TestMacierzyUprawnien(TestCase):
    def test_administrator_ma_wszystko(self):
        user = utworz_uzytkownika('admin1', 'administrator')
        for uprawnienie in (OPERACJE, FLOTA, SLOWNIKI, USUWANIE, ADMINISTRACJA):
            self.assertTrue(ma_uprawnienie(user, uprawnienie), uprawnienie)

    def test_kierownik_bez_administracji(self):
        user = utworz_uzytkownika('kier1', 'kierownik')
        for uprawnienie in (OPERACJE, FLOTA, SLOWNIKI, USUWANIE):
            self.assertTrue(ma_uprawnienie(user, uprawnienie), uprawnienie)
        self.assertFalse(ma_uprawnienie(user, ADMINISTRACJA))

    def test_pracownik_tylko_operacje(self):
        user = utworz_uzytkownika('prac1', 'pracownik')
        self.assertTrue(ma_uprawnienie(user, OPERACJE))
        for uprawnienie in (FLOTA, SLOWNIKI, USUWANIE, ADMINISTRACJA):
            self.assertFalse(ma_uprawnienie(user, uprawnienie), uprawnienie)

    def test_podglad_nic_nie_moze(self):
        user = utworz_uzytkownika('widz1', 'podglad')
        for uprawnienie in (OPERACJE, FLOTA, SLOWNIKI, USUWANIE, ADMINISTRACJA):
            self.assertFalse(ma_uprawnienie(user, uprawnienie), uprawnienie)

    def test_superuser_jest_administratorem(self):
        user = User.objects.create_superuser('root1', password='tajne123')
        self.assertEqual(rola(user), 'administrator')
        self.assertTrue(ma_uprawnienie(user, ADMINISTRACJA))

    def test_konto_bez_profilu_ma_tylko_podglad(self):
        user = utworz_uzytkownika('bezprofilu', profil=False)
        self.assertEqual(rola(user), 'podglad')
        self.assertFalse(ma_uprawnienie(user, OPERACJE))

    def test_kontekst_dla_szablonow(self):
        user = utworz_uzytkownika('prac2', 'pracownik')
        kontekst = uprawnienia_uzytkownika(user)
        self.assertTrue(kontekst['operacje'])
        self.assertFalse(kontekst['usuwanie'])
        self.assertEqual(kontekst['rola'], 'pracownik')


class TestBlokowaniaWidokow(BazaTestowa):
    """Kazda rola probuje wejsc na widoki spoza swojego zakresu."""

    ADRESY = {
        OPERACJE: '/rezerwacje/dodaj/',
        FLOTA: '/pojazdy/dodaj/',
        SLOWNIKI: '/marki/dodaj/',
        ADMINISTRACJA: '/uzytkownicy/',
    }

    def _sprawdz(self, rola_uzytkownika, dozwolone):
        user = utworz_uzytkownika(f'test_{rola_uzytkownika}', rola_uzytkownika)
        self.client.force_login(user)
        for uprawnienie, adres in self.ADRESY.items():
            oczekiwany = 200 if uprawnienie in dozwolone else 403
            self.assertEqual(
                self.client.get(adres).status_code, oczekiwany,
                f'{rola_uzytkownika} → {adres}',
            )

    def test_administrator(self):
        self._sprawdz('administrator', {OPERACJE, FLOTA, SLOWNIKI, ADMINISTRACJA})

    def test_kierownik(self):
        self._sprawdz('kierownik', {OPERACJE, FLOTA, SLOWNIKI})

    def test_pracownik(self):
        self._sprawdz('pracownik', {OPERACJE})

    def test_podglad(self):
        self._sprawdz('podglad', set())

    def test_kazda_rola_czyta_listy(self):
        for rola_uzytkownika in ('administrator', 'kierownik', 'pracownik', 'podglad'):
            user = utworz_uzytkownika(f'czyt_{rola_uzytkownika}', rola_uzytkownika)
            self.client.force_login(user)
            for adres in ('/', '/pojazdy/', '/rezerwacje/', '/zlecenia/', '/kontrahenci/', '/marki/'):
                self.assertEqual(self.client.get(adres).status_code, 200,
                                 f'{rola_uzytkownika} → {adres}')

    def test_pracownik_nie_usuwa(self):
        self.client.force_login(utworz_uzytkownika('prac3', 'pracownik'))
        odp = self.client.post(f'/usun/rezerwacja/{self.rez_wwa.pk}/')
        self.assertEqual(odp.status_code, 403)
        self.assertTrue(Rezerwacja.objects.filter(pk=self.rez_wwa.pk).exists())

    def test_kierownik_usuwa(self):
        self.client.force_login(utworz_uzytkownika('kier3', 'kierownik'))
        self.client.post(f'/usun/rezerwacja/{self.rez_wwa.pk}/')
        self.assertFalse(Rezerwacja.objects.filter(pk=self.rez_wwa.pk).exists())

    def test_podglad_nie_wydaje_pojazdu(self):
        self.client.force_login(utworz_uzytkownika('widz3', 'podglad'))
        odp = self.client.post(f'/rezerwacje/{self.rez_wwa.pk}/wydanie/', {
            'faktyczna_data_wydania': '2026-09-01T10:00',
            'przebieg_wydania': '10500', 'pojazd': self.auto_wwa.pk,
        })
        self.assertEqual(odp.status_code, 403)
        self.rez_wwa.refresh_from_db()
        self.assertEqual(self.rez_wwa.status, 'nowa')

    def test_kazdy_wchodzi_na_swoj_profil(self):
        self.client.force_login(utworz_uzytkownika('widz4', 'podglad'))
        self.assertEqual(self.client.get('/profil/').status_code, 200)


class TestOgraniczeniaOddzialu(BazaTestowa):
    def setUp(self):
        super().setUp()
        self.pracownik_wwa = utworz_uzytkownika('prac_wwa', 'pracownik', oddzial=self.warszawa)

    def test_pracownik_widzi_tylko_swoj_oddzial(self):
        self.client.force_login(self.pracownik_wwa)
        pojazdy = self.client.get('/pojazdy/').context['pojazdy']
        self.assertIn(self.auto_wwa, pojazdy)
        self.assertNotIn(self.auto_krk, pojazdy)

    def test_rezerwacje_zawezone_do_oddzialu(self):
        self.client.force_login(self.pracownik_wwa)
        rezerwacje = self.client.get('/rezerwacje/').context['rezerwacje']
        self.assertIn(self.rez_wwa, rezerwacje)
        self.assertNotIn(self.rez_krk, rezerwacje)

    def test_obcy_pojazd_daje_404(self):
        self.client.force_login(self.pracownik_wwa)
        self.assertEqual(self.client.get(f'/pojazdy/{self.auto_krk.pk}/').status_code, 404)
        self.assertEqual(self.client.get(f'/pojazdy/{self.auto_wwa.pk}/').status_code, 200)

    def test_obca_rezerwacja_daje_404(self):
        self.client.force_login(self.pracownik_wwa)
        self.assertEqual(self.client.get(f'/rezerwacje/{self.rez_krk.pk}/').status_code, 404)
        self.assertEqual(self.client.get(f'/rezerwacje/{self.rez_wwa.pk}/').status_code, 200)

    def test_nie_da_sie_edytowac_obcej_rezerwacji(self):
        self.client.force_login(self.pracownik_wwa)
        self.assertEqual(self.client.get(f'/rezerwacje/{self.rez_krk.pk}/edytuj/').status_code, 404)

    def test_kierownik_widzi_wszystkie_oddzialy(self):
        kierownik = utworz_uzytkownika('kier_wwa', 'kierownik', oddzial=self.warszawa)
        self.client.force_login(kierownik)
        pojazdy = self.client.get('/pojazdy/').context['pojazdy']
        self.assertIn(self.auto_wwa, pojazdy)
        self.assertIn(self.auto_krk, pojazdy)
        self.assertIsNone(oddzial_uzytkownika(kierownik))

    def test_pracownik_bez_oddzialu_widzi_wszystko(self):
        self.client.force_login(utworz_uzytkownika('prac_bez', 'pracownik'))
        pojazdy = self.client.get('/pojazdy/').context['pojazdy']
        self.assertIn(self.auto_wwa, pojazdy)
        self.assertIn(self.auto_krk, pojazdy)

    def test_serwis_zawezony_do_oddzialu(self):
        for pojazd in (self.auto_wwa, self.auto_krk):
            ZlecenieSerwisowe.objects.create(
                pojazd=pojazd, platnik='srodki_wlasne', typ='naprawa',
                data_przyjecia=self.teraz.date(),
            )
        self.client.force_login(self.pracownik_wwa)
        zlecenia = self.client.get('/zlecenia/').context['zlecenia']
        self.assertEqual(len(zlecenia), 1)
        self.assertEqual(zlecenia[0].pojazd, self.auto_wwa)

    def test_pulpit_liczy_tylko_swoj_oddzial(self):
        self.client.force_login(self.pracownik_wwa)
        kontekst = self.client.get('/').context
        self.assertEqual(kontekst['liczba_pojazdow'], 1)
        self.assertEqual(kontekst['liczba_rezerwacji'], 1)

    def test_kalendarz_pokazuje_tylko_swoje_pojazdy(self):
        self.client.force_login(self.pracownik_wwa)
        odp = self.client.get('/rezerwacje/kalendarz/')
        rejestracje = [w['pojazd'].numer_rejestracyjny for w in odp.context['wiersze']]
        self.assertEqual(rejestracje, ['WX1000A'])

    def test_modal_wyboru_pojazdu_zawezony(self):
        self.client.force_login(self.pracownik_wwa)
        odp = self.client.get('/rezerwacje/dodaj/')
        self.assertContains(odp, 'WX1000A')
        self.assertNotContains(odp, 'KR2000B')

    def test_nie_da_sie_podstawic_obcego_pojazdu_w_poscie(self):
        """Samo ukrycie w formularzu nie wystarcza — POST też musi być odrzucony."""
        self.client.force_login(self.pracownik_wwa)
        odp = self.client.post('/rezerwacje/dodaj/', {
            'status': 'nowa', 'typ': 'corpo', 'klient': self.klient.pk,
            'uzytkownik_pojazdu': self.kierowca.pk, 'klasa_pojazdu': self.klasa.pk,
            'pojazd': self.auto_krk.pk, 'waluta': 'PLN',
            'planowana_data_wydania': '2026-10-01T10:00',
            'planowana_data_zwrotu': '2026-10-05T10:00',
            'taki_sam_adres_zwrotu': 'on',
            'zmiany_pojazdu-TOTAL_FORMS': '0', 'zmiany_pojazdu-INITIAL_FORMS': '0',
            'zmiany_pojazdu-MIN_NUM_FORMS': '0', 'zmiany_pojazdu-MAX_NUM_FORMS': '1000',
        })
        self.assertEqual(odp.status_code, 200)
        self.assertFormError(odp.context['form'], 'pojazd',
                             'Wybierz poprawną wartość. Podana nie jest jednym z dostępnych wyborów.')
        self.assertEqual(Rezerwacja.objects.filter(pojazd=self.auto_krk).count(), 1)

    def test_zlecenie_serwisowe_nie_przyjmie_obcego_pojazdu(self):
        self.client.force_login(self.pracownik_wwa)
        odp = self.client.post('/zlecenia/dodaj/', {
            'pojazd': self.auto_krk.pk, 'platnik': 'srodki_wlasne', 'typ': 'naprawa',
            'status': 'otwarte', 'data_przyjecia': '2026-10-01',
        })
        self.assertEqual(odp.status_code, 200)
        self.assertEqual(ZlecenieSerwisowe.objects.count(), 0)


class TestZarzadzaniaKontami(BazaTestowa):
    def setUp(self):
        super().setUp()
        self.admin = utworz_uzytkownika('admin_konta', 'administrator')
        self.client.force_login(self.admin)

    def test_dodanie_uzytkownika_z_rola_i_oddzialem(self):
        odp = self.client.post('/uzytkownicy/dodaj/', {
            'first_name': 'Jan', 'last_name': 'Kowalski', 'username': 'jkowalski',
            'email': 'jan@example.com', 'password1': 'TajneHaslo1', 'password2': 'TajneHaslo1',
            'rola': 'pracownik', 'oddzial': self.warszawa.pk, 'telefon': '600100200',
        })
        self.assertEqual(odp.status_code, 302)
        nowy = User.objects.get(username='jkowalski')
        self.assertEqual(nowy.profil.rola, 'pracownik')
        self.assertEqual(nowy.profil.oddzial, self.warszawa)
        self.assertFalse(nowy.is_superuser)

    def test_rola_administratora_nadaje_superusera(self):
        self.client.post('/uzytkownicy/dodaj/', {
            'first_name': 'Ewa', 'last_name': 'Szef', 'username': 'eszef',
            'password1': 'TajneHaslo1', 'password2': 'TajneHaslo1', 'rola': 'administrator',
        })
        self.assertTrue(User.objects.get(username='eszef').is_superuser)

    def test_zmiana_roli_przez_edycje(self):
        pracownik = utworz_uzytkownika('do_awansu', 'pracownik')
        self.client.post(f'/uzytkownicy/{pracownik.pk}/edytuj/', {
            'username': 'do_awansu', 'first_name': 'A', 'last_name': 'B',
            'email': '', 'is_active': 'on', 'rola': 'kierownik', 'oddzial': '',
        })
        pracownik.profil.refresh_from_db()
        self.assertEqual(pracownik.profil.rola, 'kierownik')

    def test_karta_uzytkownika_pokazuje_role(self):
        pracownik = utworz_uzytkownika('do_podgladu', 'pracownik', oddzial=self.krakow)
        odp = self.client.get(f'/uzytkownicy/{pracownik.pk}/')
        self.assertContains(odp, 'Pracownik')
        self.assertContains(odp, 'Kraków')


class TestUkrywaniaPrzyciskow(BazaTestowa):
    def test_podglad_nie_widzi_przyciskow_dodawania(self):
        self.client.force_login(utworz_uzytkownika('widz5', 'podglad'))
        self.assertNotContains(self.client.get('/rezerwacje/'), 'Dodaj rezerwację')
        self.assertNotContains(self.client.get('/pojazdy/'), 'Dodaj pojazd')

    def test_pracownik_widzi_dodawanie_rezerwacji_ale_nie_pojazdu(self):
        self.client.force_login(utworz_uzytkownika('prac6', 'pracownik'))
        self.assertContains(self.client.get('/rezerwacje/'), 'Dodaj rezerwację')
        self.assertNotContains(self.client.get('/pojazdy/'), 'Dodaj pojazd')

    def test_pracownik_nie_widzi_przycisku_usun(self):
        self.client.force_login(utworz_uzytkownika('prac7', 'pracownik'))
        self.assertNotContains(self.client.get(f'/rezerwacje/{self.rez_wwa.pk}/'), 'Usuń')

    def test_kierownik_widzi_przycisk_usun(self):
        self.client.force_login(utworz_uzytkownika('kier7', 'kierownik'))
        self.assertContains(self.client.get(f'/rezerwacje/{self.rez_wwa.pk}/'), 'Usuń')

    def test_menu_administracji_tylko_dla_administratora(self):
        self.client.force_login(utworz_uzytkownika('kier8', 'kierownik'))
        self.assertNotContains(self.client.get('/'), 'Ustawienia firmy')
        self.client.force_login(utworz_uzytkownika('admin8', 'administrator'))
        self.assertContains(self.client.get('/'), 'Ustawienia firmy')
