import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from administracja.models import Oddzial, ProfilUzytkownika
from kontrahenci.models import Kontrahent, UzytkownikPojazdu, DodatkoweDaneKontaktowe
from pojazdy.models import Marka, ModelPojazdu, KlasaPojazdu, Konfiguracja, Pojazd
from wynajmy.models import Rezerwacja

from .models import ZlecenieSerwisowe, SzkodaBladcharska, Uszkodzenie

def utworz_uzytkownika(login, rola='kierownik', oddzial=None, haslo='tajne123'):
    """Konto testowe z profilem i rolą (konto bez profilu ma tylko podgląd)."""
    user = User.objects.create_user(login, password=haslo)
    ProfilUzytkownika.objects.create(user=user, rola=rola, oddzial=oddzial)
    return user



class BazaTestowa(TestCase):
    def setUp(self):
        self.user = utworz_uzytkownika('tester', rola='kierownik')
        self.client.force_login(self.user)

        self.teraz = timezone.now().replace(microsecond=0)
        marka = Marka.objects.create(nazwa='Skoda')
        model = ModelPojazdu.objects.create(marka=marka, nazwa='Octavia')
        self.klasa = KlasaPojazdu.objects.create(nazwa='C')
        konfiguracja = Konfiguracja.objects.create(
            model=model, wersja_wyposazenia='Style', typ_nadwozia='kombi',
            klasa_pojazdu=self.klasa, pojemnosc_silnika='1.5', moc_km=150,
            rodzaj_paliwa='benzyna', typ_skrzyni='manualna', naped='fwd',
        )
        self.pojazd = Pojazd.objects.create(
            konfiguracja=konfiguracja, numer_rejestracyjny='WX1000A',
            rok_produkcji=2023, data_zakupu=self.teraz.date(), przebieg_km=10000,
        )
        self.warsztat = Kontrahent.objects.create(nazwa_firmy='Serwis ABC', typ_serwis=True)
        self.klient = Kontrahent.objects.create(nazwa_firmy='Klient sp. z o.o.', typ_klient=True)
        self.uzytkownik = UzytkownikPojazdu.objects.create(imie='Anna', nazwisko='Nowak')


class TestZlecen(BazaTestowa):
    def test_dodanie_zlecenia(self):
        odp = self.client.post('/zlecenia/dodaj/', {
            'pojazd': self.pojazd.pk, 'platnik': 'srodki_wlasne', 'typ': 'przeglad',
            'status': 'otwarte', 'data_przyjecia': '2026-09-01', 'warsztat': self.warsztat.pk,
        })
        self.assertEqual(odp.status_code, 302)
        self.assertEqual(ZlecenieSerwisowe.objects.count(), 1)

    def test_koszt_bierze_rzeczywisty_przed_planowanym(self):
        z = ZlecenieSerwisowe.objects.create(
            pojazd=self.pojazd, platnik='srodki_wlasne', typ='naprawa',
            data_przyjecia=self.teraz.date(), planowany_koszt_netto=500,
        )
        self.assertEqual(z.koszt, 500)
        z.rzeczywisty_koszt_netto = 620
        self.assertEqual(z.koszt, 620)

    def test_najemca_podpowiada_sie_z_trwajacej_rezerwacji(self):
        Rezerwacja.objects.create(
            status='w_toku', typ='corpo', klient=self.klient, uzytkownik_pojazdu=self.uzytkownik,
            klasa_pojazdu=self.klasa, pojazd=self.pojazd,
            planowana_data_wydania=self.teraz - datetime.timedelta(days=1),
            planowana_data_zwrotu=self.teraz + datetime.timedelta(days=5),
        )
        odp = self.client.get(f'/zlecenia/dodaj/?pojazd={self.pojazd.pk}')
        initial = odp.context['form'].initial
        self.assertTrue(initial['w_trakcie_wynajmu'])
        self.assertEqual(initial['najemca'], self.klient.pk)

    def test_bez_rezerwacji_podpowiada_sam_pojazd(self):
        odp = self.client.get(f'/zlecenia/dodaj/?pojazd={self.pojazd.pk}')
        initial = odp.context['form'].initial
        self.assertEqual(initial['pojazd'], str(self.pojazd.pk))
        self.assertNotIn('najemca', initial)

    def test_filtrowanie_po_statusie(self):
        for status in ('otwarte', 'zamkniete'):
            ZlecenieSerwisowe.objects.create(
                pojazd=self.pojazd, platnik='srodki_wlasne', typ='naprawa',
                status=status, data_przyjecia=self.teraz.date(),
            )
        odp = self.client.get('/zlecenia/', {'status': 'otwarte'})
        self.assertEqual(len(odp.context['zlecenia']), 1)

    def test_wyszukiwanie_po_rejestracji(self):
        ZlecenieSerwisowe.objects.create(
            pojazd=self.pojazd, platnik='srodki_wlasne', typ='naprawa',
            data_przyjecia=self.teraz.date(),
        )
        self.assertEqual(len(self.client.get('/zlecenia/', {'szukaj': 'WX1000'}).context['zlecenia']), 1)
        self.assertEqual(len(self.client.get('/zlecenia/', {'szukaj': 'ZZZ'}).context['zlecenia']), 0)


class TestSzkodIUszkodzen(BazaTestowa):
    def test_filtrowanie_uszkodzen_po_naprawieniu(self):
        Uszkodzenie.objects.create(pojazd=self.pojazd, opis='Rysa na drzwiach')
        Uszkodzenie.objects.create(pojazd=self.pojazd, opis='Pęknięta szyba', naprawione=True)
        self.assertEqual(len(self.client.get('/uszkodzenia/', {'naprawione': 'nie'}).context['uszkodzenia']), 1)
        self.assertEqual(len(self.client.get('/uszkodzenia/', {'naprawione': 'tak'}).context['uszkodzenia']), 1)
        self.assertEqual(len(self.client.get('/uszkodzenia/').context['uszkodzenia']), 2)

    def test_status_uszkodzenia(self):
        u = Uszkodzenie.objects.create(pojazd=self.pojazd, opis='Rysa')
        self.assertEqual(u.status_opis, 'Do naprawy')
        self.assertEqual(u.kolor_statusu, 'uwaga')
        u.naprawione = True
        self.assertEqual(u.status_opis, 'Naprawione')
        self.assertEqual(u.kolor_statusu, 'ok')

    def test_karta_pojazdu_pokazuje_serwis(self):
        ZlecenieSerwisowe.objects.create(
            pojazd=self.pojazd, platnik='srodki_wlasne', typ='opony',
            data_przyjecia=self.teraz.date(),
        )
        SzkodaBladcharska.objects.create(pojazd=self.pojazd, platnik='ac', numer_szkody='SZ/1')
        Uszkodzenie.objects.create(pojazd=self.pojazd, opis='Rysa na masce')

        odp = self.client.get(f'/pojazdy/{self.pojazd.pk}/')
        self.assertEqual(len(odp.context['zlecenia']), 1)
        self.assertEqual(len(odp.context['szkody']), 1)
        self.assertEqual(len(odp.context['uszkodzenia']), 1)
        self.assertContains(odp, 'SZ/1')


class TestUsuwania(BazaTestowa):
    def test_usuniecie_rekordu_bez_powiazan(self):
        u = Uszkodzenie.objects.create(pojazd=self.pojazd, opis='Rysa')
        odp = self.client.post(f'/usun/uszkodzenie/{u.pk}/')
        self.assertRedirects(odp, '/uszkodzenia/')
        self.assertFalse(Uszkodzenie.objects.filter(pk=u.pk).exists())

    def test_get_pokazuje_potwierdzenie_i_nie_usuwa(self):
        u = Uszkodzenie.objects.create(pojazd=self.pojazd, opis='Rysa')
        odp = self.client.get(f'/usun/uszkodzenie/{u.pk}/')
        self.assertEqual(odp.status_code, 200)
        self.assertContains(odp, 'Czy na pewno')
        self.assertTrue(Uszkodzenie.objects.filter(pk=u.pk).exists())

    def test_chroniony_rekord_nie_znika(self):
        ZlecenieSerwisowe.objects.create(
            pojazd=self.pojazd, platnik='srodki_wlasne', typ='naprawa',
            data_przyjecia=self.teraz.date(),
        )
        odp = self.client.post(f'/usun/pojazd/{self.pojazd.pk}/', follow=True)
        self.assertTrue(Pojazd.objects.filter(pk=self.pojazd.pk).exists())
        self.assertContains(odp, 'Nie można usunąć')

    def test_nieznany_typ_daje_404(self):
        self.assertEqual(self.client.get('/usun/cosdziwnego/1/').status_code, 404)

    def test_kierownik_nie_usuwa_kont(self):
        # konta i oddzialy to obszar administracji, nie zwyklego usuwania
        odp = self.client.post(f'/usun/uzytkownik/{self.user.pk}/')
        self.assertEqual(odp.status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_administrator_nie_usuwa_wlasnego_konta(self):
        admin = utworz_uzytkownika('szef', rola='administrator')
        self.client.force_login(admin)
        odp = self.client.post(f'/usun/uzytkownik/{admin.pk}/', follow=True)
        self.assertTrue(User.objects.filter(pk=admin.pk).exists())
        self.assertContains(odp, 'własnego konta')

    def test_potwierdzenie_wymienia_powiazania(self):
        Uszkodzenie.objects.create(pojazd=self.pojazd, opis='Rysa')
        odp = self.client.get(f'/usun/pojazd/{self.pojazd.pk}/')
        self.assertContains(odp, 'Uszkodzenia: 1')


class TestKontrahenta(BazaTestowa):
    def _dane(self, **nadpisz):
        dane = {
            'stan': 'aktywny', 'nazwa_firmy': 'Nowa Firma sp. z o.o.', 'kod_kraj': 'PL', 'kraj': 'Polska',
            'dodatkowe_kontakty-TOTAL_FORMS': '2',
            'dodatkowe_kontakty-INITIAL_FORMS': '0',
            'dodatkowe_kontakty-MIN_NUM_FORMS': '0',
            'dodatkowe_kontakty-MAX_NUM_FORMS': '1000',
            'dodatkowe_kontakty-0-typ': 'telefon',
            'dodatkowe_kontakty-0-wartosc': '+48 22 111 22 33',
            'dodatkowe_kontakty-0-opis': 'księgowość',
            'dodatkowe_kontakty-1-typ': '',
            'dodatkowe_kontakty-1-wartosc': '',
            'dodatkowe_kontakty-1-opis': '',
        }
        dane.update(nadpisz)
        return dane

    def test_dodanie_kontrahenta_z_kontaktami(self):
        odp = self.client.post('/kontrahenci/dodaj/', self._dane())
        self.assertEqual(odp.status_code, 302)
        kontrahent = Kontrahent.objects.get(nazwa_firmy='Nowa Firma sp. z o.o.')
        self.assertEqual(kontrahent.dodatkowe_kontakty.count(), 1)
        self.assertEqual(kontrahent.dodatkowe_kontakty.first().wartosc, '+48 22 111 22 33')

    def test_kontakty_widoczne_na_karcie(self):
        DodatkoweDaneKontaktowe.objects.create(kontrahent=self.klient, typ='email', wartosc='biuro@example.com')
        odp = self.client.get(f'/kontrahenci/{self.klient.pk}/')
        self.assertContains(odp, 'biuro@example.com')


class TestProfilu(BazaTestowa):
    def test_zapis_danych_konta(self):
        odp = self.client.post('/profil/', {
            'zapisz_dane': '1', 'first_name': 'Jan', 'last_name': 'Kowalski',
            'email': 'jan@example.com', 'telefon': '600100200',
        })
        self.assertRedirects(odp, '/profil/')
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Jan')
        self.assertEqual(self.user.profil.telefon, '600100200')

    def test_zmiana_hasla_nie_wylogowuje(self):
        odp = self.client.post('/profil/', {
            'zmien_haslo': '1', 'old_password': 'tajne123',
            'new_password1': 'InneTajne987', 'new_password2': 'InneTajne987',
        })
        self.assertRedirects(odp, '/profil/')
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('InneTajne987'))
        # sesja nadal wazna — brak przekierowania na logowanie
        self.assertEqual(self.client.get('/profil/').status_code, 200)

    def test_bledne_stare_haslo_odrzucone(self):
        odp = self.client.post('/profil/', {
            'zmien_haslo': '1', 'old_password': 'zle',
            'new_password1': 'InneTajne987', 'new_password2': 'InneTajne987',
        })
        self.assertEqual(odp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('tajne123'))
