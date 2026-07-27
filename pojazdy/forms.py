from django import forms
from .models import Pojazd, Konfiguracja, Marka, ModelPojazdu, Polisa, KlasaPojazdu

class PojazdForm(forms.ModelForm):
    class Meta:
        model = Pojazd
        fields = [
            'konfiguracja',
            'numer_rejestracyjny',
            'rok_produkcji',
            'data_zakupu',
            'przebieg_km',
            'vin',
            'status',
            'stan',
            'oddzial',
            'dostawca',
            'wlasciciel',
            'wspolwlasciciel',
            'data_przegladu',
            'data_ubezpieczenia',
        ]
        widgets = {
            'data_zakupu': forms.DateInput(attrs={'type': 'date'}),
            'data_przegladu': forms.DateInput(attrs={'type': 'date'}),
            'data_ubezpieczenia': forms.DateInput(attrs={'type': 'date'}),
            'status': forms.RadioSelect,
            'stan': forms.RadioSelect,
            'numer_rejestracyjny': forms.TextInput(attrs={'placeholder': 'np. WA 12345'}),
            'vin': forms.TextInput(attrs={'placeholder': '17 znaków'}),
            'rok_produkcji': forms.NumberInput(attrs={'placeholder': 'np. 2024'}),
            'przebieg_km': forms.NumberInput(attrs={'placeholder': 'km'}),
        }

class PolisaForm(forms.ModelForm):
    class Meta:
        model = Polisa
        fields = [
            'pojazd',
            'rodzaj_oc',
            'rodzaj_ac',
            'rodzaj_nnw',
            'rodzaj_assistance',
            'numer_umowy_generalnej',
            'numer_polisy',
            'data_od',
            'data_do',
            'ubezpieczyciel',
            'uwagi',
            'skan',
        ]
        
        widgets = {
            'data_od': forms.DateInput(attrs={'type': 'date'}),
            'data_do': forms.DateInput(attrs={'type': 'date'}),
            'numer_polisy': forms.TextInput(attrs={'placeholder': 'np. POL/2026/001'}),
            'numer_umowy_generalnej': forms.TextInput(attrs={'placeholder': 'np. UG/2026/01'}),
            'ubezpieczyciel': forms.TextInput(attrs={'placeholder': 'np. PZU'}),
            'uwagi': forms.Textarea(attrs={'rows': 3}),
        }

class MarkaForm(forms.ModelForm):
    class Meta:
        model = Marka
        fields = ['nazwa']

class ModelPojazduForm(forms.ModelForm):
    class Meta:
        model = ModelPojazdu
        fields = ['marka', 'nazwa']

class KlasaPojazduForm(forms.ModelForm):
    class Meta:
        model = KlasaPojazdu
        fields = ['nazwa']

class KonfiguracjaForm(forms.ModelForm):
    class Meta:
        model = Konfiguracja
        fields = [
            'model',
            'wersja_wyposazenia',
            'typ_nadwozia',
            'klasa_pojazdu',
            'liczba_drzwi',
            'maksymalna_liczba_pasazerow',
            'pojemnosc_silnika',
            'moc_km',
            'moc_kw',
            'rodzaj_paliwa',
            'typ_skrzyni',
            'naped',
            'pojemnosc_baku',
            'spalanie_l100km',
            'co2_gkm',
            'interwał_przeglądu_km',
            'interwał_przeglądu_miesięcy',
        ]
        widgets = {
            'wersja_wyposazenia': forms.TextInput(attrs={'placeholder': 'np. Style'}),
            'pojemnosc_silnika': forms.TextInput(attrs={'placeholder': 'np. 1.5 TSI'}),
            'moc_km': forms.NumberInput(attrs={'placeholder': 'KM'}),
            'moc_kw': forms.NumberInput(attrs={'placeholder': 'puste — wyliczy się z KM'}),
            'pojemnosc_baku': forms.NumberInput(attrs={'placeholder': 'litry'}),
            'spalanie_l100km': forms.NumberInput(attrs={'placeholder': 'l/100km'}),
            'co2_gkm': forms.NumberInput(attrs={'placeholder': 'g/km'}),
        }
