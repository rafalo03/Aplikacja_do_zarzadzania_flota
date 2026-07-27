from django import forms
from .models import ZlecenieSerwisowe, SzkodaBladcharska, Uszkodzenie
from kontrahenci.models import Kontrahent

class ZlecenieSerwisoweForms(forms.ModelForm):
    class Meta:
        model = ZlecenieSerwisowe
        fields = [
            'pojazd', 'w_trakcie_wynajmu', 'najemca', 'warsztat',
            'platnik', 'typ', 'status', 'data_przyjecia',
            'planowana_data_zakonczenia', 'opis',
            'planowany_koszt_netto', 'rzeczywisty_koszt_netto', 'przebieg',
        ]
        widgets = {
            'data_przyjecia': forms.DateInput(attrs={'type': 'date'}),
            'planowana_data_zakonczenia': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['warsztat'].queryset = Kontrahent.objects.filter(typ_serwis=True)

class SzkodaBlacharskaForm(forms.ModelForm):
    class Meta:
        model = SzkodaBladcharska
        fields = [
            'pojazd', 'w_trakcie_wynajmu', 'najemca', 'platnik',
            'numer_szkody', 'warsztat', 'status',
            'planowany_koszt_netto', 'rzeczywisty_koszt_netto',
            'przebieg', 'data_zdarzenia', 'opis',
        ]
        widgets = {
            'data_zdarzenia': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['warsztat'].queryset = Kontrahent.objects.filter(typ_serwis=True)
class UszkodzenieForm(forms.ModelForm):
    class Meta:
        model = Uszkodzenie
        fields = ['pojazd', 'opis', 'zdjecie', 'zglaszajacy', 'naprawione', 'koszt_naprawy']
