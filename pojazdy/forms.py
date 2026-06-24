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