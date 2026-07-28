from django import forms
from .models import Kontrahent, UzytkownikPojazdu


class KontrahentForm(forms.ModelForm):
    class Meta:
        model = Kontrahent
        fields = [
            'stan', 'nazwa_firmy', 'rodzaj_dzialalnosci',
            'typ_klient', 'typ_broker', 'typ_dealer', 'typ_dostawca_finansowania',
            'typ_obsluga_serwisowa', 'typ_serwis', 'typ_wlasciciel_pojazdow',
            'nip', 'regon', 'numer_krs', 'kod_kraj',
            'telefon', 'email', 'email_faktury',
            'ulica', 'numer_domu', 'numer_mieszkania',
            'kod_pocztowy', 'miasto', 'wojewodztwo', 'kraj',
            'opiekun', 'uwagi',
        ]
        widgets = {
            'uwagi': forms.Textarea(attrs={'rows': 3}),
        }


class UzytkownikPojazduForm(forms.ModelForm):
    class Meta:
        model = UzytkownikPojazdu
        fields = [
            'imie', 'nazwisko', 'pesel', 'telefon', 'email',
            'ulica', 'numer_domu', 'numer_mieszkania',
            'kod_pocztowy', 'miasto', 'kraj',
            'numer_dokumentu', 'numer_prawa_jazdy', 'data_waznosci_prawa_jazdy',
        ]
        widgets = {
            'data_waznosci_prawa_jazdy': forms.DateInput(attrs={'type': 'date'}),
        }
