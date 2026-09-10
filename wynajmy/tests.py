import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from administracja.models import Oddzial, ProfilUzytkownika
from kontrahenci.models import Kontrahent, UzytkownikPojazdu
from pojazdy.models import Marka, ModelPojazdu, KlasaPojazdu, Konfiguracja, Pojazd

from .models import Cennik, PozycjaCennika, Rezerwacja, ZmianaPojazdu, znajdz_cennik

def utworz_uzytkownika(login, rola='kierownik', oddzial=None, haslo='tajne123'):
    """Konto testowe z profilem i rolą (konto bez profilu ma tylko podgląd)."""
    user = User.objects.create_user(login, password=haslo)
    ProfilUzytkownika.objects.create(user=user, rola=rola, oddzial=oddzial)
    return user



class BazaTestowa(TestCase):
    """Wspolny zestaw danych: klient, uzytkownik, dwa pojazdy klasy B i cennik."""

    def setUp(self):
        self.teraz = timezone.now().replace(microsecond=0)
        self.klient = Kontrahent.objects.create(nazwa_firmy='Testowa sp. z o.o.', typ_klient=True)
        self.uzytkownik = UzytkownikPojazdu.objects.create(imie='Anna', nazwisko='Nowak')
        self.klasa = KlasaPojazdu.objects.create(nazwa='B')
        self.klasa_c = KlasaPojazdu.objects.create(nazwa='C')

        marka = Marka.objects.create(nazwa='Skoda')
        model = ModelPojazdu.objects.create(marka=marka, nazwa='Octavia')
        self.konfiguracja = Konfiguracja.objects.create(
            model=model, wersja_wyposazenia='Style', typ_nadwozia='kombi',
            klasa_pojazdu=self.klasa, pojemnosc_silnika='1.5', moc_km=150,
            rodzaj_paliwa='benzyna', typ_skrzyni='manualna', naped='fwd',
        )
        self.oddzial = Oddzial.objects.create(nazwa='Warszawa')
        self.pojazd = self._pojazd('WX1000A')
        self.pojazd2 = self._pojazd('WX2000B')

        self.cennik = Cennik.objects.create(nazwa='Standardowy', typ_stawki='dzienna', waluta='PLN')
        PozycjaCennika.objects.create(cennik=self.cennik, klasa_pojazdu=self.klasa, cena=200)

    def _pojazd(self, rejestracja):
        return Pojazd.objects.create(
            konfiguracja=self.konfiguracja, numer_rejestracyjny=rejestracja,
            rok_produkcji=2023, data_zakupu=self.teraz.date(), przebieg_km=10000,
            oddzial=self.oddzial,
        )

    def _rezerwacja(self, **nadpisz):
        dane = dict(
            typ='corpo', klient=self.klient, uzytkownik_pojazdu=self.uzytkownik,
            klasa_pojazdu=self.klasa, pojazd=self.pojazd, cennik=self.cennik,
            cena_jednostkowa=200,
            planowana_data_wydania=self.teraz,
            planowana_data_zwrotu=self.teraz + datetime.timedelta(days=3),
        )
        dane.update(nadpisz)
        return Rezerwacja.objects.create(**dane)


class TestNumeracji(BazaTestowa):
    def test_numer_nadawany_automatycznie(self):
        r = self._rezerwacja()
        self.assertEqual(r.numer, f'REZ/{timezone.now().year}/001')

    def test_kolejne_numery_rosna(self):
        self._rezerwacja()
        druga = self._rezerwacja(pojazd=self.pojazd2)
        self.assertEqual(druga.numer, f'REZ/{timezone.now().year}/002')


class TestWyliczen(BazaTestowa):
    def test_liczba_dni_i_wartosc(self):
        r = self._rezerwacja()
        self.assertEqual(r.liczba_dni, 3)
        self.assertEqual(str(r.wartosc_calkowita), '600.00')

    def test_rozpoczety_dzien_liczy_sie_jako_pelny(self):
        r = self._rezerwacja(planowana_data_zwrotu=self.teraz + datetime.timedelta(days=2, hours=3))
        self.assertEqual(r.liczba_dni, 3)

    def test_stawka_tygodniowa_liczy_tygodnie(self):
        cennik = Cennik.objects.create(nazwa='Tygodniowy', typ_stawki='tygodniowa')
        PozycjaCennika.objects.create(cennik=cennik, klasa_pojazdu=self.klasa, cena=1000)
        r = self._rezerwacja(
            cennik=cennik, cena_jednostkowa=1000,
            planowana_data_zwrotu=self.teraz + datetime.timedelta(days=10),
        )
        self.assertEqual(r.liczba_dni, 10)
        self.assertEqual(r.liczba_jednostek, 2)
        self.assertEqual(str(r.wartosc_calkowita), '2000.00')

    def test_faktyczne_daty_maja_pierwszenstwo(self):
        r = self._rezerwacja()
        r.faktyczna_data_wydania = self.teraz
        r.faktyczna_data_zwrotu = self.teraz + datetime.timedelta(days=5)
        self.assertEqual(r.liczba_dni, 5)

    def test_przejechane_kilometry(self):
        r = self._rezerwacja(przebieg_wydania=10000, przebieg_zwrotu=10850)
        self.assertEqual(r.przejechane_km, 850)


class TestWalidacji(BazaTestowa):
    def test_zwrot_przed_wydaniem_odrzucony(self):
        r = self._rezerwacja(planowana_data_zwrotu=self.teraz - datetime.timedelta(days=1))
        with self.assertRaises(ValidationError) as ctx:
            r.full_clean()
        self.assertIn('planowana_data_zwrotu', ctx.exception.error_dict)

    def test_podstawienie_wymaga_adresu(self):
        r = self._rezerwacja(podstawienie=True)
        with self.assertRaises(ValidationError) as ctx:
            r.full_clean()
        self.assertIn('adres_podstawienia', ctx.exception.error_dict)

    def test_inny_adres_zwrotu_wymaga_adresu(self):
        r = self._rezerwacja(taki_sam_adres_zwrotu=False)
        with self.assertRaises(ValidationError) as ctx:
            r.full_clean()
        self.assertIn('adres_zwrotu', ctx.exception.error_dict)

    def test_klasa_pojazdu_musi_sie_zgadzac(self):
        r = self._rezerwacja(klasa_pojazdu=self.klasa_c)
        with self.assertRaises(ValidationError) as ctx:
            r.full_clean()
        self.assertIn('pojazd', ctx.exception.error_dict)

    def test_przebieg_zwrotu_nie_moze_zmalec(self):
        r = self._rezerwacja(przebieg_wydania=10000, przebieg_zwrotu=9000)
        with self.assertRaises(ValidationError) as ctx:
            r.full_clean()
        self.assertIn('przebieg_zwrotu', ctx.exception.error_dict)


class TestKolizji(BazaTestowa):
    def test_nakladajacy_sie_termin_jest_odrzucany(self):
        self._rezerwacja()
        druga = Rezerwacja(
            typ='corpo', klient=self.klient, uzytkownik_pojazdu=self.uzytkownik,
            klasa_pojazdu=self.klasa, pojazd=self.pojazd,
            planowana_data_wydania=self.teraz + datetime.timedelta(days=1),
            planowana_data_zwrotu=self.teraz + datetime.timedelta(days=5),
        )
        with self.assertRaises(ValidationError) as ctx:
            druga.full_clean()
        self.assertIn('pojazd', ctx.exception.error_dict)

    def test_termin_stykajacy_sie_koncem_jest_dozwolony(self):
        self._rezerwacja()
        druga = Rezerwacja(
            typ='corpo', klient=self.klient, uzytkownik_pojazdu=self.uzytkownik,
            klasa_pojazdu=self.klasa, pojazd=self.pojazd,
            planowana_data_wydania=self.teraz + datetime.timedelta(days=3),
            planowana_data_zwrotu=self.teraz + datetime.timedelta(days=6),
        )
        druga.full_clean()  # nie powinno rzucic wyjatku

    def test_anulowana_rezerwacja_nie_blokuje(self):
        self._rezerwacja(status='anulowana')
        druga = Rezerwacja(
            typ='corpo', klient=self.klient, uzytkownik_pojazdu=self.uzytkownik,
            klasa_pojazdu=self.klasa, pojazd=self.pojazd,
            planowana_data_wydania=self.teraz + datetime.timedelta(days=1),
            planowana_data_zwrotu=self.teraz + datetime.timedelta(days=2),
        )
        druga.full_clean()

    def test_edycja_wlasnej_rezerwacji_nie_koliduje_sama_ze_soba(self):
        r = self._rezerwacja()
        r.planowana_data_zwrotu = self.teraz + datetime.timedelta(days=4)
        r.full_clean()

    def test_zamiana_pojazdu_tez_blokuje_termin(self):
        r = self._rezerwacja()
        ZmianaPojazdu.objects.create(
            rezerwacja=r, pojazd=self.pojazd2, data_zamiany=self.teraz + datetime.timedelta(days=1)
        )
        druga = Rezerwacja(
            typ='corpo', klient=self.klient, uzytkownik_pojazdu=self.uzytkownik,
            klasa_pojazdu=self.klasa, pojazd=self.pojazd2,
            planowana_data_wydania=self.teraz + datetime.timedelta(days=1),
            planowana_data_zwrotu=self.teraz + datetime.timedelta(days=2),
        )
        with self.assertRaises(ValidationError):
            druga.full_clean()

    def test_wolne_pojazdy_pomija_zajete(self):
        self._rezerwacja()
        wolne = Rezerwacja.wolne_pojazdy(
            self.teraz + datetime.timedelta(days=1),
            self.teraz + datetime.timedelta(days=2),
            klasa_pojazdu=self.klasa,
        )
        self.assertNotIn(self.pojazd, wolne)
        self.assertIn(self.pojazd2, wolne)


class TestCennika(BazaTestowa):
    def test_cennik_klienta_ma_pierwszenstwo(self):
        wlasny = Cennik.objects.create(nazwa='Dla klienta', kontrahent=self.klient, typ_stawki='dzienna')
        PozycjaCennika.objects.create(cennik=wlasny, klasa_pojazdu=self.klasa, cena=150)
        self.assertEqual(znajdz_cennik(self.klient, self.klasa), wlasny)

    def test_bez_cennika_klienta_wraca_standardowy(self):
        self.assertEqual(znajdz_cennik(self.klient, self.klasa), self.cennik)

    def test_pomija_cennik_bez_pozycji_dla_klasy(self):
        self.assertIsNone(znajdz_cennik(self.klient, self.klasa_c))

    def test_nieaktywny_cennik_jest_pomijany(self):
        self.cennik.aktywny = False
        self.cennik.save()
        self.assertIsNone(znajdz_cennik(self.klient, self.klasa))


class TestAkcji(BazaTestowa):
    def test_wydanie_zmienia_statusy(self):
        r = self._rezerwacja(status='potwierdzona')
        r.wydaj(self.teraz, 10500)
        self.pojazd.refresh_from_db()
        self.assertEqual(r.status, 'w_toku')
        self.assertEqual(r.przebieg_wydania, 10500)
        self.assertEqual(self.pojazd.status, 'wynajety')
        self.assertEqual(self.pojazd.przebieg_km, 10500)

    def test_zwrot_zwalnia_pojazd(self):
        r = self._rezerwacja(status='potwierdzona')
        r.wydaj(self.teraz, 10500)
        r.zwroc(self.teraz + datetime.timedelta(days=3), 11200)
        self.pojazd.refresh_from_db()
        self.assertEqual(r.status, 'zakonczona')
        self.assertEqual(r.przejechane_km, 700)
        self.assertEqual(self.pojazd.status, 'dostepny')
        self.assertEqual(self.pojazd.przebieg_km, 11200)

    def test_anulowanie_zwalnia_pojazd(self):
        r = self._rezerwacja(status='potwierdzona')
        r.wydaj(self.teraz, 10500)
        r.anuluj()
        self.pojazd.refresh_from_db()
        self.assertEqual(r.status, 'anulowana')
        self.assertEqual(self.pojazd.status, 'dostepny')

    def test_opoznienie_wykrywane(self):
        r = self._rezerwacja(
            status='w_toku',
            planowana_data_wydania=self.teraz - datetime.timedelta(days=5),
            planowana_data_zwrotu=self.teraz - datetime.timedelta(days=1),
        )
        self.assertTrue(r.czy_opozniona)

    def test_zwrot_oddaje_pojazd_po_zamianie(self):
        r = self._rezerwacja(status='potwierdzona')
        r.wydaj(self.teraz, 10500)
        ZmianaPojazdu.objects.create(
            rezerwacja=r, pojazd=self.pojazd2, data_zamiany=self.teraz - datetime.timedelta(hours=1)
        )
        r.zwroc(self.teraz + datetime.timedelta(days=1), 10900)
        self.pojazd2.refresh_from_db()
        self.assertEqual(self.pojazd2.status, 'dostepny')


class TestWidokow(BazaTestowa):
    def setUp(self):
        super().setUp()
        self.user = utworz_uzytkownika('tester', rola='kierownik')
        self.client.force_login(self.user)

    def _dane_formularza(self, **nadpisz):
        dane = {
            'status': 'nowa', 'typ': 'corpo', 'klient': self.klient.pk,
            'uzytkownik_pojazdu': self.uzytkownik.pk, 'klasa_pojazdu': self.klasa.pk,
            'pojazd': self.pojazd.pk, 'waluta': 'PLN',
            'planowana_data_wydania': '2026-09-01T10:00',
            'planowana_data_zwrotu': '2026-09-05T10:00',
            'taki_sam_adres_zwrotu': 'on',
            'zmiany_pojazdu-TOTAL_FORMS': '0',
            'zmiany_pojazdu-INITIAL_FORMS': '0',
            'zmiany_pojazdu-MIN_NUM_FORMS': '0',
            'zmiany_pojazdu-MAX_NUM_FORMS': '1000',
        }
        dane.update(nadpisz)
        return dane

    def test_dodanie_rezerwacji_przez_formularz(self):
        odp = self.client.post('/rezerwacje/dodaj/', self._dane_formularza())
        self.assertEqual(odp.status_code, 302)
        r = Rezerwacja.objects.get()
        self.assertEqual(r.liczba_dni, 4)
        # cennik i cena podstawily sie automatycznie
        self.assertEqual(r.cennik, self.cennik)
        self.assertEqual(str(r.cena_jednostkowa), '200.00')

    def test_formularz_odrzuca_kolizje(self):
        self._rezerwacja(
            planowana_data_wydania=timezone.make_aware(datetime.datetime(2026, 9, 2, 8, 0)),
            planowana_data_zwrotu=timezone.make_aware(datetime.datetime(2026, 9, 4, 8, 0)),
        )
        odp = self.client.post('/rezerwacje/dodaj/', self._dane_formularza())
        self.assertEqual(odp.status_code, 200)
        self.assertContains(odp, 'już zarezerwowany')
        self.assertEqual(Rezerwacja.objects.count(), 1)

    def test_protokol_wydania_i_zwrotu(self):
        r = self._rezerwacja(status='potwierdzona')
        odp = self.client.post(f'/rezerwacje/{r.pk}/wydanie/', {
            'faktyczna_data_wydania': '2026-09-01T10:00',
            'przebieg_wydania': '10500',
            'pojazd': self.pojazd.pk,
        })
        self.assertEqual(odp.status_code, 302)
        r.refresh_from_db()
        self.assertEqual(r.status, 'w_toku')

        odp = self.client.post(f'/rezerwacje/{r.pk}/zwrot/', {
            'faktyczna_data_zwrotu': '2026-09-04T10:00',
            'przebieg_zwrotu': '11000',
        })
        self.assertEqual(odp.status_code, 302)
        r.refresh_from_db()
        self.assertEqual(r.status, 'zakonczona')
        self.assertEqual(r.przejechane_km, 500)

    def test_nie_mozna_wydac_zakonczonej(self):
        r = self._rezerwacja(status='zakonczona')
        odp = self.client.get(f'/rezerwacje/{r.pk}/wydanie/')
        self.assertRedirects(odp, f'/rezerwacje/{r.pk}/')

    def test_anulowanie_tylko_postem(self):
        r = self._rezerwacja()
        self.client.get(f'/rezerwacje/{r.pk}/anuluj/')
        r.refresh_from_db()
        self.assertEqual(r.status, 'nowa')

        self.client.post(f'/rezerwacje/{r.pk}/anuluj/')
        r.refresh_from_db()
        self.assertEqual(r.status, 'anulowana')

    def test_api_wyceny(self):
        odp = self.client.get('/api/wycena/', {
            'klasa': self.klasa.pk, 'klient': self.klient.pk,
            'od': '2026-09-01T10:00', 'do': '2026-09-05T10:00',
        })
        dane = odp.json()
        self.assertEqual(dane['cena'], '200.00')
        self.assertEqual(dane['dni'], 4)
        self.assertEqual(dane['wartosc'], '800.00')

    def test_api_dostepnosci_zwraca_zajete(self):
        r = self._rezerwacja(
            planowana_data_wydania=timezone.make_aware(datetime.datetime(2026, 9, 2, 8, 0)),
            planowana_data_zwrotu=timezone.make_aware(datetime.datetime(2026, 9, 4, 8, 0)),
        )
        odp = self.client.get('/api/dostepnosc/', {'od': '2026-09-01T10:00', 'do': '2026-09-05T10:00'})
        dane = odp.json()
        self.assertIn(str(self.pojazd.pk), dane['zajete'])
        self.assertIn(r.numer, dane['zajete'][str(self.pojazd.pk)])

    def test_kalendarz_pokazuje_rezerwacje(self):
        r = self._rezerwacja()
        odp = self.client.get('/rezerwacje/kalendarz/')
        self.assertEqual(odp.status_code, 200)
        self.assertContains(odp, r.klient.nazwa_firmy)

    def test_filtrowanie_listy_po_statusie(self):
        self._rezerwacja(status='anulowana')
        self._rezerwacja(pojazd=self.pojazd2, status='nowa')
        odp = self.client.get('/rezerwacje/', {'status': 'aktywne'})
        self.assertEqual(len(odp.context['rezerwacje']), 1)

    def test_pulpit_liczy_rezerwacje(self):
        self._rezerwacja()
        odp = self.client.get('/')
        self.assertEqual(odp.context['liczba_rezerwacji'], 1)
