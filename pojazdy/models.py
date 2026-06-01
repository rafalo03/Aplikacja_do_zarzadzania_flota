from django.db import models

class Marka(models.Model):
    nazwa = models.CharField(max_length=50)

    def __str__(self):
        return self.nazwa

    class Meta:
        verbose_name = 'Marka'
        verbose_name_plural = 'Marki'


class ModelPojazdu(models.Model):
    marka = models.ForeignKey(Marka, on_delete=models.CASCADE, related_name='modele')
    nazwa = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.marka} {self.nazwa}"
    
    class Meta:
        verbose_name = 'Model pojazdu'
        verbose_name_plural = 'Modele pojazdów'


class Konfiguracja(models.Model):
    TYP_NADWOZIA = [
        ('kombi', 'Kombi'),
        ('suv', 'SUV'),
        ('crossover', 'Crossover'),
        ('sedan', 'Sedan'),
        ('hatchback', 'Hatchback'),
        ('limuzyna', 'Limuzyna'),
        ('van', 'Van'),
        ('bus', 'Bus'),
    ]

    TYP_SKRZYNI = [
        ('manualna', 'Manualna'),
        ('automatyczna', 'Automatyczna'),
    ]

    NAPED = [
        ('fwd', 'Przednie koła'),
        ('rwd', 'Tylne koła'),
        ('awd', 'Wszystkie koła'),
    ]

    model = models.ForeignKey(ModelPojazdu, on_delete=models.CASCADE, related_name='konfiguracje')
    wersja_wyposazenia = models.CharField(max_length=50)
    typ_nadwozia = models.CharField(max_length=20, choices=TYP_NADWOZIA)
    liczba_drzwi = models.IntegerField(default=5)
    maksymalna_liczba_pasazerow = models.IntegerField(default=5)
    pojemnosc_silnika = models.CharField(max_length=20)
    moc_km = models.IntegerField()
    moc_kw = models.IntegerField(blank=True, null=True)
    rodzaj_paliwa = models.CharField(max_length=20, choices=[
        ('benzyna', 'Benzyna'),
        ('diesel', 'Diesel'),
        ('hybryda', 'Hybryda'),
        ('elektryk', 'Elektryk'),
        ('benzyna_lpg', 'Benzyna z LPG'),
    ])
    typ_skrzyni = models.CharField(max_length=20, choices=TYP_SKRZYNI)
    naped = models.CharField(max_length=10, choices=NAPED)
    pojemnosc_baku = models.IntegerField(null=True, blank=True, help_text='Litry')
    spalanie_l100km = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    co2_gkm = models.IntegerField(null=True, blank=True)
    interwał_przeglądu_km = models.IntegerField(default=15000)
    interwał_przeglądu_miesięcy = models.IntegerField(default=12)

    def save(self, *args, **kwargs):
        if self.moc_km and not self.moc_kw:
            self.moc_kw = round(self.moc_km * 0.7355)
        elif self.moc_kw and not self.moc_km:
            self.moc_km = round(self.moc_kw / 0.7355)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.model} {self.wersja_wyposazenia}"

    class Meta:
        verbose_name = 'Konfiguracja'
        verbose_name_plural = 'Konfiguracje'


class Pojazd(models.Model):
    konfiguracja = models.ForeignKey(Konfiguracja, on_delete=models.PROTECT, related_name='pojazdy')
    numer_rejestracyjny = models.CharField(max_length=20, unique=True)
    rok_produkcji = models.IntegerField()
    data_zakupu = models.DateField()
    przebieg_km = models.IntegerField(default=0)
    vin = models.CharField(max_length=17, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('dostepny', 'Dostępny'),
        ('wynajety', 'Wynajęty'),
        ('serwis', 'W serwisie'),
    ], default='dostepny')
    data_przegladu = models.DateField(null=True, blank=True)
    data_ubezpieczenia = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.konfiguracja} ({self.numer_rejestracyjny})"

    class Meta:
        verbose_name = 'Pojazd'
        verbose_name_plural = 'Pojazdy'