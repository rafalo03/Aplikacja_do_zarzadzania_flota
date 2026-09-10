from django.db import models
from pojazdy.models import Pojazd
from kontrahenci.models import Kontrahent


class ZlecenieSerwisowe(models.Model):
    TYP_ZLECENIA = [
        ('przeglad', 'Przegląd'),
        ('naprawa', 'Naprawa'),
        ('opony', 'Opony'),
        ('holowanie', 'Holowanie'),
        ('samochod_zastepczy', 'Samochód zastępczy'),
        ('inne', 'Inne'),
    ]

    STATUS = [
        ('otwarte', 'Otwarte'),
        ('w_realizacji', 'W realizacji'),
        ('zamkniete', 'Zamknięte'),
        ('anulowane', 'Anulowane'),
    ]

    PLATNIK = [
        ('srodki_wlasne', 'Środki własne'),
        ('gwarancja', 'Gwarancja'),
        ('wlasciciel', 'Właściciel pojazdu'),
        ('leasing', 'Leasing'),
    ]

    pojazd = models.ForeignKey(Pojazd, on_delete=models.PROTECT, related_name='zlecenia_serwisowe')
    w_trakcie_wynajmu = models.BooleanField(default=False, verbose_name='W trakcie wynajmu')
    najemca = models.ForeignKey(Kontrahent, on_delete=models.SET_NULL, null=True, blank=True, related_name='zlecenia_jako_najemca', verbose_name='Najemca')
    warsztat = models.ForeignKey(Kontrahent, on_delete=models.SET_NULL, null=True, blank=True, related_name='zlecenia_jako_warsztat', verbose_name='Warsztat')
    platnik = models.CharField(max_length=20, choices=PLATNIK)
    typ = models.CharField(max_length=30, choices=TYP_ZLECENIA)
    status = models.CharField(max_length=20, choices=STATUS, default='otwarte')
    data_przyjecia = models.DateField()
    planowana_data_zakonczenia = models.DateField(null=True, blank=True)
    opis = models.TextField(null=True, blank=True)
    planowany_koszt_netto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rzeczywisty_koszt_netto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    przebieg = models.IntegerField(null=True, blank=True)

    KOLORY_STATUSOW = {
        'otwarte': 'info',
        'w_realizacji': 'akcent',
        'zamkniete': 'ok',
        'anulowane': 'blad',
    }

    def __str__(self):
        return f"Zlecenie {self.pk} - {self.pojazd} ({self.get_typ_display()})"

    @property
    def kolor_statusu(self):
        return self.KOLORY_STATUSOW.get(self.status, 'neutralny')

    @property
    def koszt(self):
        """Koszt rzeczywisty, a jesli go nie ma - planowany."""
        return self.rzeczywisty_koszt_netto if self.rzeczywisty_koszt_netto is not None else self.planowany_koszt_netto

    class Meta:
        verbose_name = 'Zlecenie serwisowe'
        verbose_name_plural = 'Zlecenia serwisowe'
        ordering = ['-data_przyjecia', '-pk']


class SzkodaBladcharska(models.Model):
    STATUS = [
        ('zgloszona', 'Zgłoszona'),
        ('w_realizacji', 'W realizacji'),
        ('zamknieta', 'Zamknięta'),
        ('anulowana', 'Anulowana'),
    ]

    PLATNIK = [
        ('srodki_wlasne', 'Środki własne'),
        ('ac', 'AC'),
        ('oc_sprawcy', 'OC sprawcy'),
    ]

    pojazd = models.ForeignKey(Pojazd, on_delete=models.PROTECT, related_name='szkody')
    w_trakcie_wynajmu = models.BooleanField(default=False, verbose_name='W trakcie wynajmu')
    najemca = models.ForeignKey(Kontrahent, on_delete=models.SET_NULL, null=True, blank=True, related_name='szkody_jako_najemca', verbose_name='Najemca')
    platnik = models.CharField(max_length=20, choices=PLATNIK)
    numer_szkody = models.CharField(max_length=50, null=True, blank=True)
    warsztat = models.ForeignKey(Kontrahent, on_delete=models.SET_NULL, null=True, blank=True, related_name='szkody_jako_warsztat', verbose_name='Warsztat')
    status = models.CharField(max_length=20, choices=STATUS, default='zgloszona')
    planowany_koszt_netto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rzeczywisty_koszt_netto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    przebieg = models.IntegerField(null=True, blank=True)
    data_zdarzenia = models.DateField(null=True, blank=True)
    opis = models.TextField(null=True, blank=True)

    KOLORY_STATUSOW = {
        'zgloszona': 'uwaga',
        'w_realizacji': 'akcent',
        'zamknieta': 'ok',
        'anulowana': 'blad',
    }

    def __str__(self):
        return f"Szkoda {self.pk} - {self.pojazd}"

    @property
    def kolor_statusu(self):
        return self.KOLORY_STATUSOW.get(self.status, 'neutralny')

    @property
    def koszt(self):
        return self.rzeczywisty_koszt_netto if self.rzeczywisty_koszt_netto is not None else self.planowany_koszt_netto

    class Meta:
        verbose_name = 'Szkoda blacharska'
        verbose_name_plural = 'Szkody blacharskie'
        ordering = ['-data_zdarzenia', '-pk']


class Uszkodzenie(models.Model):
    pojazd = models.ForeignKey(Pojazd, on_delete=models.PROTECT, related_name='uszkodzenia')
    data_wykrycia = models.DateField(auto_now_add=True)
    opis = models.TextField()
    zdjecie = models.ImageField(upload_to='uszkodzenia/', null=True, blank=True)
    zglaszajacy = models.CharField(max_length=100, null=True, blank=True)
    naprawione = models.BooleanField(default=False)
    koszt_naprawy = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Uszkodzenie {self.pk} - {self.pojazd}"

    @property
    def kolor_statusu(self):
        return 'ok' if self.naprawione else 'uwaga'

    @property
    def status_opis(self):
        return 'Naprawione' if self.naprawione else 'Do naprawy'

    class Meta:
        verbose_name = 'Uszkodzenie'
        verbose_name_plural = 'Uszkodzenia'
        ordering = ['-data_wykrycia', '-pk']