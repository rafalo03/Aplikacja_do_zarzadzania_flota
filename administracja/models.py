from django.db import models
from django.contrib.auth.models import User

class ProfilUzytkownika(models.Model):
    ROLE = [
        ('administrator', 'Administrator'),
        ('kierownik', 'Kierownik'),
        ('pracownik', 'Pracownik'),
        ('podglad', 'Podgląd'),
    ]

    OPIS_ROL = {
        'administrator': 'Pełny dostęp, w tym zarządzanie użytkownikami i oddziałami.',
        'kierownik': 'Wszystko oprócz administracji; może usuwać rekordy i prowadzić słowniki.',
        'pracownik': 'Prowadzi rezerwacje, serwis i kontrahentów. Bez usuwania, pojazdów i słowników.',
        'podglad': 'Tylko odczyt.',
    }

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil')
    telefon = models.CharField(max_length=20, null=True, blank=True)
    rola = models.CharField(max_length=20, choices=ROLE, default='pracownik')
    oddzial = models.ForeignKey(
        'administracja.Oddzial',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uzytkownicy',
        verbose_name='Oddział',
        help_text='Puste = dostęp do danych wszystkich oddziałów.',
    )

    def __str__(self):
        return f"Profil {self.user.get_full_name()}"

    class Meta:
        verbose_name = 'Profil użytkownika'
        verbose_name_plural = 'Profile użytkowników'

class UkladTabeli(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uklady_tabel')
    tabela = models.CharField(max_length=50)
    nazwa = models.CharField(max_length=100)
    dane = models.JSONField()
    aktywny = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} – {self.tabela} – {self.nazwa}"

    class Meta:
        unique_together = ('user', 'tabela', 'nazwa')
        verbose_name = 'Układ tabeli'
        verbose_name_plural = 'Układy tabel'

class Oddzial(models.Model):
    nazwa = models.CharField(max_length=100, unique=True)
    adres = models.CharField(max_length=200, null=True, blank=True)
    telefon = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.nazwa

    class Meta:
        verbose_name = 'Oddział'
        verbose_name_plural = 'Oddziały'
        ordering = ['nazwa']
