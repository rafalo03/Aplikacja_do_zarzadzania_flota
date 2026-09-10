from django import forms
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.forms import inlineformset_factory
from django.utils import timezone

from .models import Rezerwacja, Cennik, PozycjaCennika, ZmianaPojazdu, znajdz_cennik
from kontrahenci.models import Kontrahent
from administracja.models import Oddzial
from administracja.uprawnienia import WyborPojazduZOddzialu

DATETIME_LOCAL = {'type': 'datetime-local'}
FORMAT_LOCAL = '%Y-%m-%dT%H:%M'
# Przegladarkowy input datetime-local wysyla format ISO z litera T
FORMATY_WEJSCIA = [FORMAT_LOCAL, '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']


def pole_daty(label=None, required=True):
    return forms.DateTimeField(
        label=label,
        required=required,
        input_formats=FORMATY_WEJSCIA,
        widget=forms.DateTimeInput(attrs=DATETIME_LOCAL, format=FORMAT_LOCAL),
    )


class MapowanieBledowModelu:
    """Błędy z Model.clean() dotyczące pól spoza formularza pokazuje jako ogólne.

    Bez tego Django podnosi ValueError (HTTP 500), gdy walidacja modelu wskaże
    pole, którego dany formularz nie zawiera — np. protokół wydania nie ma pola
    z adresem zwrotu.
    """

    def _update_errors(self, errors):
        if hasattr(errors, 'error_dict'):
            przemapowane = {}
            for pole, komunikaty in errors.error_dict.items():
                docelowe = pole if pole == NON_FIELD_ERRORS or pole in self.fields else NON_FIELD_ERRORS
                przemapowane.setdefault(docelowe, []).extend(komunikaty)
            errors = ValidationError(przemapowane)
        super()._update_errors(errors)


class RezerwacjaForm(WyborPojazduZOddzialu, MapowanieBledowModelu, forms.ModelForm):
    planowana_data_wydania = pole_daty('Planowana data wydania')
    planowana_data_zwrotu = pole_daty('Planowana data zwrotu')

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
            'uwagi': forms.Textarea(attrs={'rows': 2}),
            'uwagi_faktura': forms.Textarea(attrs={'rows': 2}),
            'uwagi_zwrot': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['klient'].queryset = Kontrahent.objects.filter(typ_klient=True)
        self.fields['cennik'].queryset = Cennik.objects.filter(aktywny=True).select_related('kontrahent')
        self.fields['cennik'].help_text = 'Puste = cennik dobierze się automatycznie po kliencie i klasie.'
        self.fields['cena_jednostkowa'].help_text = 'Puste = cena z cennika.'
        oddzialy = [('', '---------')] + [(o.nazwa, o.nazwa) for o in Oddzial.objects.all()]
        self.fields['oddzial_wydania'].widget = forms.Select(choices=oddzialy)

    def clean(self):
        dane = super().clean()
        klient = dane.get('klient')
        klasa = dane.get('klasa_pojazdu')

        # Cennik i cena uzupelniaja sie same, jesli uzytkownik ich nie podal
        if not dane.get('cennik') and klasa:
            dane['cennik'] = znajdz_cennik(klient, klasa)
        cennik = dane.get('cennik')
        if dane.get('cena_jednostkowa') is None and cennik:
            cena = cennik.cena_dla_klasy(klasa)
            if cena is not None:
                dane['cena_jednostkowa'] = cena
        if cennik and not dane.get('waluta'):
            dane['waluta'] = cennik.waluta
        return dane


class WydanieForm(WyborPojazduZOddzialu, MapowanieBledowModelu, forms.ModelForm):
    faktyczna_data_wydania = pole_daty('Data wydania')

    class Meta:
        model = Rezerwacja
        fields = ['faktyczna_data_wydania', 'przebieg_wydania', 'pojazd']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pojazd'].required = True
        self.fields['pojazd'].help_text = 'Pojazd faktycznie wydany klientowi.'
        self.fields['przebieg_wydania'].required = True
        if not self.initial.get('faktyczna_data_wydania'):
            self.initial['faktyczna_data_wydania'] = timezone.localtime().replace(second=0, microsecond=0)
        if self.initial.get('przebieg_wydania') is None and self.instance.pojazd_id:
            self.initial['przebieg_wydania'] = self.instance.pojazd.przebieg_km


class ZwrotForm(MapowanieBledowModelu, forms.ModelForm):
    faktyczna_data_zwrotu = pole_daty('Data zwrotu')

    class Meta:
        model = Rezerwacja
        fields = ['faktyczna_data_zwrotu', 'przebieg_zwrotu', 'uwagi_zwrot']
        widgets = {'uwagi_zwrot': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['przebieg_zwrotu'].required = True
        if not self.initial.get('faktyczna_data_zwrotu'):
            self.initial['faktyczna_data_zwrotu'] = timezone.localtime().replace(second=0, microsecond=0)
        if self.initial.get('przebieg_zwrotu') is None:
            self.initial['przebieg_zwrotu'] = self.instance.przebieg_wydania

    def clean_faktyczna_data_zwrotu(self):
        data = self.cleaned_data['faktyczna_data_zwrotu']
        wydanie = self.instance.faktyczna_data_wydania
        if wydanie and data and data < wydanie:
            raise forms.ValidationError('Zwrot nie może być wcześniejszy niż wydanie pojazdu.')
        return data


class CennikForm(forms.ModelForm):
    class Meta:
        model = Cennik
        fields = ['nazwa', 'kontrahent', 'typ_stawki', 'waluta', 'aktywny']


PozycjaCennikaFormSet = inlineformset_factory(
    Cennik, PozycjaCennika,
    fields=['klasa_pojazdu', 'cena'],
    extra=3, can_delete=True,
)

class ZmianaPojazduForm(WyborPojazduZOddzialu, forms.ModelForm):
    data_zamiany = pole_daty('Data zamiany')

    class Meta:
        model = ZmianaPojazdu
        fields = ['pojazd', 'data_zamiany']


ZmianaPojazduFormSet = inlineformset_factory(
    Rezerwacja, ZmianaPojazdu,
    form=ZmianaPojazduForm,
    extra=1, can_delete=True,
)
