from django.db import models
from pojazdy.models import Pojazd, Konfiguracja, KlasaPojazdu
from kontrahenci.models import Kontrahent, UzytkownikPojazdu


class Cennik(models.Model):
    TYP_STAWKI = [
        ('dzienna', 'Dzienna'),
        ('tygodniowa', 'Tygodniowa'),
        ('miesieczna', 'Miesięczna'),
    ]

    WALUTA = [
        ('PLN', 'PLN'),
        ('EUR', 'EUR'),
    ]

    kontrahent = models.ForeignKey(
        Kontrahent,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cenniki',
        verbose_name='Firma (puste = standardowy)'
    )
    nazwa = models.CharField(max_length=100)
    typ_stawki = models.CharField(max_length=20, choices=TYP_STAWKI)
    waluta = models.CharField(max_length=3, choices=WALUTA, default='PLN')
    aktywny = models.BooleanField(default=True)

    def __str__(self):
        if self.kontrahent:
            return f"{self.nazwa} - {self.kontrahent}"
        return f"{self.nazwa} (standardowy)"

    class Meta:
        verbose_name = 'Cennik'
        verbose_name_plural = 'Cenniki'


class PozycjaCennika(models.Model):
    cennik = models.ForeignKey(Cennik, on_delete=models.CASCADE, related_name='pozycje')
    klasa_pojazdu = models.ForeignKey(KlasaPojazdu, on_delete=models.PROTECT, related_name='pozycje_cennika')
    cena = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cennik} - {self.klasa_pojazdu}: {self.cena}"

    class Meta:
        verbose_name = 'Pozycja cennika'
        verbose_name_plural = 'Pozycje cennika'
        unique_together = ('cennik', 'klasa_pojazdu')


class Rezerwacja(models.Model):
    TYP = [
        ('corpo', 'Corpo'),
        ('konsumencki', 'Wynajem konsumencki'),
    ]

    WALUTA = [
        ('PLN', 'PLN'),
        ('EUR', 'EUR'),
    ]

    STATUS = [
        ('nowa', 'Nowa'),
        ('potwierdzona', 'Potwierdzona'),
        ('w_toku', 'W toku'),
        ('zakonczona', 'Zakończona'),
        ('anulowana', 'Anulowana'),
    ]

    # Podstawowe dane
    status = models.CharField(max_length=20, choices=STATUS, default='nowa')
    typ = models.CharField(max_length=20, choices=TYP)
    klient = models.ForeignKey(Kontrahent, on_delete=models.PROTECT, related_name='rezerwacje')
    uzytkownik_pojazdu = models.ForeignKey(UzytkownikPojazdu, on_delete=models.PROTECT, related_name='rezerwacje')
    waluta = models.CharField(max_length=3, choices=WALUTA, default='PLN')
    mpk_klienta = models.CharField(max_length=50, null=True, blank=True)
    uwagi = models.TextField(null=True, blank=True)
    uwagi_faktura = models.TextField(null=True, blank=True)

    # Pojazd
    klasa_pojazdu = models.ForeignKey(KlasaPojazdu, on_delete=models.PROTECT, related_name='rezerwacje')
    pojazd = models.ForeignKey(Pojazd, on_delete=models.PROTECT, null=True, blank=True, related_name='rezerwacje')

    # Cennik i cena
    cennik = models.ForeignKey(Cennik, on_delete=models.SET_NULL, null=True, blank=True, related_name='rezerwacje')
    cena_jednostkowa = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Wydanie
    planowana_data_wydania = models.DateTimeField()
    oddzial_wydania = models.CharField(max_length=100, null=True, blank=True)
    adres_podstawienia = models.CharField(max_length=200, null=True, blank=True)
    podstawienie = models.BooleanField(default=False)

    # Zwrot
    planowana_data_zwrotu = models.DateTimeField()
    taki_sam_adres_zwrotu = models.BooleanField(default=True)
    adres_zwrotu = models.CharField(max_length=200, null=True, blank=True)
    uwagi_zwrot = models.TextField(null=True, blank=True)

    data_utworzenia = models.DateTimeField(auto_now_add=True)
    data_modyfikacji = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Rezerwacja {self.pk} - {self.klient} ({self.status})"

    class Meta:
        verbose_name = 'Rezerwacja'
        verbose_name_plural = 'Rezerwacje'


class ZmianaPojazdu(models.Model):
    rezerwacja = models.ForeignKey(Rezerwacja, on_delete=models.CASCADE, related_name='zmiany_pojazdu')
    pojazd = models.ForeignKey(Pojazd, on_delete=models.PROTECT, related_name='zmiany_rezerwacji')
    data_zamiany = models.DateTimeField(verbose_name='Data zamiany')

    def __str__(self):
        return f"{self.rezerwacja_id}: {self.pojazd} od {self.data_zamiany}"

    class Meta:
        verbose_name = 'Zamiana pojazdu'
        verbose_name_plural = 'Zamiany pojazdów'
        ordering = ['data_zamiany']