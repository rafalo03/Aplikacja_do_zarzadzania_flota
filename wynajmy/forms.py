from django import forms
from django.forms import inlineformset_factory
from .models import Rezerwacja, Cennik, PozycjaCennika, ZmianaPojazdu
from kontrahenci.models import Kontrahent
from administracja.models import Oddzial


class RezerwacjaForm(forms.ModelForm):
    class Meta:
        model = Rezerwacja
        fields = [
            'status', 'typ', 'klient', 'uzytkownik_pojazdu', 'mpk_klienta',
            'klasa_pojazdu', 'pojazd',
            'cennik', 'cena_jednostkowa', 'waluta',
            'planowana_data_wydania', 'oddzial_wydania', 'podstawienie', 'adres_podstawienia',
            'planowana_data_zwrotu', 'taki_sam_adres_zwrotu', 'adres_zwrotu',
            'uwagi', 'uwagi_faktura', 'uwagi_zwrot',
        ]
        widgets = {
            'planowana_data_wydania': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'planowana_data_zwrotu': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'uwagi': forms.Textarea(attrs={'rows': 2}),
            'uwagi_faktura': forms.Textarea(attrs={'rows': 2}),
            'uwagi_zwrot': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['klient'].queryset = Kontrahent.objects.filter(typ_klient=True)
        oddzialy = [('', '---------')] + [(o.nazwa, o.nazwa) for o in Oddzial.objects.all()]
        self.fields['oddzial_wydania'].widget = forms.Select(choices=oddzialy)


class CennikForm(forms.ModelForm):
    class Meta:
        model = Cennik
        fields = ['nazwa', 'kontrahent', 'typ_stawki', 'waluta', 'aktywny']


PozycjaCennikaFormSet = inlineformset_factory(
    Cennik, PozycjaCennika,
    fields=['klasa_pojazdu', 'cena'],
    extra=3, can_delete=True,
)

ZmianaPojazduFormSet = inlineformset_factory(
    Rezerwacja, ZmianaPojazdu,
    fields=['pojazd', 'data_zamiany'],
    widgets={
        'data_zamiany': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
    },
    extra=1, can_delete=True,
)
