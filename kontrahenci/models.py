from django.db import models


class Kontrahent(models.Model):
    STAN = [
        ('aktywny', 'Aktywny'),
        ('nieaktywny', 'Nieaktywny'),
    ]

    TYP = [
        ('klient', 'Klient'),
        ('broker', 'Broker'),
        ('dealer', 'Dealer'),
        ('dostawca_finansowania', 'Dostawca finansowania'),
        ('obsluga_serwisowa', 'Obsługa serwisowa'),
        ('serwis', 'Serwis'),
        ('wlasciciel_pojazdow', 'Właściciel pojazdów'),
    ]

    RODZAJ_DZIALALNOSCI = [
        ('sp_zoo', 'Sp. z o.o.'),
        ('sa', 'S.A.'),
        ('jdg', 'Jednoosobowa działalność gospodarcza'),
        ('spolka_jawna', 'Spółka jawna'),
        ('spolka_komandytowa', 'Spółka komandytowa'),
        ('inne', 'Inne'),
    ]

    stan = models.CharField(max_length=20, choices=STAN, default='aktywny')
    typ_klient = models.BooleanField(default=False, verbose_name='Klient')
    typ_broker = models.BooleanField(default=False, verbose_name='Broker')
    typ_dealer = models.BooleanField(default=False, verbose_name='Dealer')
    typ_dostawca_finansowania = models.BooleanField(default=False, verbose_name='Dostawca finansowania')
    typ_obsluga_serwisowa = models.BooleanField(default=False, verbose_name='Obsługa serwisowa')
    typ_serwis = models.BooleanField(default=False, verbose_name='Serwis')
    typ_wlasciciel_pojazdow = models.BooleanField(default=False, verbose_name='Właściciel pojazdów')
    nazwa_firmy = models.CharField(max_length=200)
    rodzaj_dzialalnosci = models.CharField(max_length=30, choices=RODZAJ_DZIALALNOSCI, null=True, blank=True)
    nip = models.CharField(max_length=10, unique=True, null=True, blank=True)
    regon = models.CharField(max_length=14, null=True, blank=True)
    numer_krs = models.CharField(max_length=10, null=True, blank=True)
    kod_kraj = models.CharField(max_length=3, default='PL')
    telefon = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    email_faktury = models.EmailField(null=True, blank=True)
    ulica = models.CharField(max_length=100, null=True, blank=True)
    numer_domu = models.CharField(max_length=10, null=True, blank=True)
    numer_mieszkania = models.CharField(max_length=10, null=True, blank=True)
    kod_pocztowy = models.CharField(max_length=10, null=True, blank=True)
    miasto = models.CharField(max_length=100, null=True, blank=True)
    wojewodztwo = models.CharField(max_length=50, null=True, blank=True)
    kraj = models.CharField(max_length=50, default='Polska')
    opiekun = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='kontrahenci',
        verbose_name='Opiekun klienta'
    )

    uwagi = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.nazwa_firmy

    class Meta:
        verbose_name = 'Kontrahent'
        verbose_name_plural = 'Kontrahenci'


class DodatkoweDaneKontaktowe(models.Model):
    TYP_KONTAKTU = [
        ('telefon', 'Telefon'),
        ('email', 'Email'),
        ('fax', 'Fax'),
        ('inne', 'Inne'),
    ]

    kontrahent = models.ForeignKey(Kontrahent, on_delete=models.CASCADE, related_name='dodatkowe_kontakty')
    typ = models.CharField(max_length=20, choices=TYP_KONTAKTU)
    wartosc = models.CharField(max_length=100)
    opis = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.kontrahent} - {self.typ}: {self.wartosc}"

    class Meta:
        verbose_name = 'Dodatkowe dane kontaktowe'
        verbose_name_plural = 'Dodatkowe dane kontaktowe'