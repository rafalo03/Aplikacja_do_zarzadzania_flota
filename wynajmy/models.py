from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

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

    def cena_dla_klasy(self, klasa_pojazdu):
        """Cena z cennika dla danej klasy pojazdu albo None."""
        if not klasa_pojazdu:
            return None
        pozycja = self.pozycje.filter(klasa_pojazdu=klasa_pojazdu).first()
        return pozycja.cena if pozycja else None

    class Meta:
        verbose_name = 'Cennik'
        verbose_name_plural = 'Cenniki'


def znajdz_cennik(klient, klasa_pojazdu=None):
    """Cennik klienta, a jesli go nie ma - cennik standardowy.

    Gdy podano klase, wybierany jest tylko cennik ktory ma dla niej pozycje.
    """
    cenniki = Cennik.objects.filter(aktywny=True)
    if klasa_pojazdu:
        cenniki = cenniki.filter(pozycje__klasa_pojazdu=klasa_pojazdu)
    if klient:
        wlasny = cenniki.filter(kontrahent=klient).first()
        if wlasny:
            return wlasny
    return cenniki.filter(kontrahent__isnull=True).first()


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

    # Statusy w ktorych rezerwacja blokuje pojazd w danym terminie
    STATUSY_BLOKUJACE = ('nowa', 'potwierdzona', 'w_toku')

    # Kolory odznak statusow uzywane w szablonach
    KOLORY_STATUSOW = {
        'nowa': 'info',
        'potwierdzona': 'ok',
        'w_toku': 'akcent',
        'zakonczona': 'neutralny',
        'anulowana': 'blad',
    }

    # Podstawowe dane
    numer = models.CharField(max_length=20, unique=True, editable=False, blank=True)
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
    faktyczna_data_wydania = models.DateTimeField(null=True, blank=True)
    przebieg_wydania = models.IntegerField(null=True, blank=True, verbose_name='Przebieg przy wydaniu (km)')

    # Zwrot
    planowana_data_zwrotu = models.DateTimeField()
    taki_sam_adres_zwrotu = models.BooleanField(default=True)
    adres_zwrotu = models.CharField(max_length=200, null=True, blank=True)
    uwagi_zwrot = models.TextField(null=True, blank=True)
    faktyczna_data_zwrotu = models.DateTimeField(null=True, blank=True)
    przebieg_zwrotu = models.IntegerField(null=True, blank=True, verbose_name='Przebieg przy zwrocie (km)')

    data_utworzenia = models.DateTimeField(auto_now_add=True)
    data_modyfikacji = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.numer or f'Rezerwacja {self.pk}'} - {self.klient}"

    # ---------- wyliczenia ----------

    @property
    def liczba_dni(self):
        """Liczba dni najmu - rozpoczety dzien liczy sie jako pelny, minimum 1."""
        koniec = self.faktyczna_data_zwrotu or self.planowana_data_zwrotu
        poczatek = self.faktyczna_data_wydania or self.planowana_data_wydania
        if not koniec or not poczatek:
            return 0
        sekundy = (koniec - poczatek).total_seconds()
        if sekundy <= 0:
            return 0
        return max(1, -(-int(sekundy) // 86400))

    @property
    def liczba_jednostek(self):
        """Liczba jednostek rozliczeniowych wg typu stawki cennika."""
        dni = self.liczba_dni
        typ = self.cennik.typ_stawki if self.cennik else 'dzienna'
        if typ == 'tygodniowa':
            return max(1, -(-dni // 7))
        if typ == 'miesieczna':
            return max(1, -(-dni // 30))
        return dni

    @property
    def wartosc_calkowita(self):
        if self.cena_jednostkowa is None:
            return None
        return (self.cena_jednostkowa * Decimal(self.liczba_jednostek)).quantize(Decimal('0.01'))

    @property
    def przejechane_km(self):
        if self.przebieg_wydania is None or self.przebieg_zwrotu is None:
            return None
        return self.przebieg_zwrotu - self.przebieg_wydania

    @property
    def kolor_statusu(self):
        return self.KOLORY_STATUSOW.get(self.status, 'neutralny')

    @property
    def czy_opozniona(self):
        """Pojazd wydany, termin zwrotu minal, a auto nie wrocilo."""
        return self.status == 'w_toku' and self.planowana_data_zwrotu < timezone.now()

    @property
    def pojazd_w_terminie(self):
        """Pojazd obowiazujacy na dzis - uwzglednia zamiany pojazdu."""
        zamiana = self.zmiany_pojazdu.filter(data_zamiany__lte=timezone.now()).order_by('-data_zamiany').first()
        return zamiana.pojazd if zamiana else self.pojazd

    # ---------- kolizje terminow ----------

    @classmethod
    def kolidujace(cls, pojazd, od, do, pomin_pk=None):
        """Rezerwacje blokujace dany pojazd w podanym oknie czasowym."""
        if not pojazd or not od or not do:
            return cls.objects.none()
        qs = cls.objects.filter(
            status__in=cls.STATUSY_BLOKUJACE,
            planowana_data_wydania__lt=do,
            planowana_data_zwrotu__gt=od,
        ).filter(Q(pojazd=pojazd) | Q(zmiany_pojazdu__pojazd=pojazd)).distinct()
        if pomin_pk:
            qs = qs.exclude(pk=pomin_pk)
        return qs

    @classmethod
    def wolne_pojazdy(cls, od, do, klasa_pojazdu=None, pomin_pk=None):
        """Pojazdy bez kolidujacej rezerwacji w podanym terminie."""
        pojazdy = Pojazd.objects.exclude(stan='wylaczony')
        if klasa_pojazdu:
            pojazdy = pojazdy.filter(konfiguracja__klasa_pojazdu=klasa_pojazdu)
        if not od or not do:
            return pojazdy
        zajete = cls.objects.filter(
            status__in=cls.STATUSY_BLOKUJACE,
            planowana_data_wydania__lt=do,
            planowana_data_zwrotu__gt=od,
        )
        if pomin_pk:
            zajete = zajete.exclude(pk=pomin_pk)
        zajete_id = set(zajete.exclude(pojazd__isnull=True).values_list('pojazd_id', flat=True))
        zajete_id |= set(ZmianaPojazdu.objects.filter(rezerwacja__in=zajete).values_list('pojazd_id', flat=True))
        return pojazdy.exclude(pk__in=zajete_id)

    # ---------- walidacja ----------

    def clean(self):
        bledy = {}

        if self.planowana_data_wydania and self.planowana_data_zwrotu:
            if self.planowana_data_zwrotu <= self.planowana_data_wydania:
                bledy['planowana_data_zwrotu'] = 'Data zwrotu musi być późniejsza niż data wydania.'

        if self.podstawienie and not self.adres_podstawienia:
            bledy['adres_podstawienia'] = 'Przy podstawieniu podaj adres podstawienia.'

        if not self.taki_sam_adres_zwrotu and not self.adres_zwrotu:
            bledy['adres_zwrotu'] = 'Podaj adres zwrotu albo zaznacz „taki sam adres zwrotu”.'

        if self.pojazd and self.klasa_pojazdu_id:
            klasa_pojazdu_auta = self.pojazd.konfiguracja.klasa_pojazdu_id
            if klasa_pojazdu_auta and klasa_pojazdu_auta != self.klasa_pojazdu_id:
                bledy['pojazd'] = (
                    f'Pojazd należy do klasy „{self.pojazd.konfiguracja.klasa_pojazdu}”, '
                    f'a rezerwacja dotyczy klasy „{self.klasa_pojazdu}”.'
                )

        if self.pojazd and self.status in self.STATUSY_BLOKUJACE:
            kolizje = self.kolidujace(
                self.pojazd, self.planowana_data_wydania, self.planowana_data_zwrotu, pomin_pk=self.pk
            )
            konflikt = kolizje.first()
            if konflikt:
                bledy['pojazd'] = (
                    f'Pojazd jest już zarezerwowany ({konflikt.numer or konflikt.pk}) '
                    f'w terminie {konflikt.planowana_data_wydania:%d.%m.%Y %H:%M} '
                    f'– {konflikt.planowana_data_zwrotu:%d.%m.%Y %H:%M}.'
                )

        if self.przebieg_wydania is not None and self.przebieg_zwrotu is not None:
            if self.przebieg_zwrotu < self.przebieg_wydania:
                bledy['przebieg_zwrotu'] = 'Przebieg przy zwrocie nie może być mniejszy niż przy wydaniu.'

        if bledy:
            raise ValidationError(bledy)

    def save(self, *args, **kwargs):
        if not self.numer:
            rok = timezone.now().year
            prefiks = f'REZ/{rok}/'
            ostatni = (
                Rezerwacja.objects.filter(numer__startswith=prefiks)
                .order_by('-numer').values_list('numer', flat=True).first()
            )
            kolejny = int(ostatni.rsplit('/', 1)[1]) + 1 if ostatni else 1
            self.numer = f'{prefiks}{kolejny:03d}'
        super().save(*args, **kwargs)

    # ---------- akcje ----------

    def wydaj(self, data=None, przebieg=None):
        """Wydanie pojazdu klientowi."""
        self.faktyczna_data_wydania = data or timezone.now()
        if przebieg is not None:
            self.przebieg_wydania = przebieg
        self.status = 'w_toku'
        self.save()
        if self.pojazd:
            self.pojazd.status = 'wynajety'
            if przebieg is not None:
                self.pojazd.przebieg_km = przebieg
            self.pojazd.save()

    def zwroc(self, data=None, przebieg=None):
        """Przyjecie zwrotu pojazdu."""
        self.faktyczna_data_zwrotu = data or timezone.now()
        if przebieg is not None:
            self.przebieg_zwrotu = przebieg
        self.status = 'zakonczona'
        self.save()
        pojazd = self.pojazd_w_terminie or self.pojazd
        if pojazd:
            pojazd.status = 'dostepny'
            if przebieg is not None:
                pojazd.przebieg_km = przebieg
            pojazd.save()

    def anuluj(self):
        self.status = 'anulowana'
        self.save()
        if self.pojazd and self.pojazd.status == 'wynajety':
            self.pojazd.status = 'dostepny'
            self.pojazd.save()

    class Meta:
        verbose_name = 'Rezerwacja'
        verbose_name_plural = 'Rezerwacje'
        ordering = ['-planowana_data_wydania']


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