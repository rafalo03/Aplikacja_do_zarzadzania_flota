from django import forms
from django.contrib.auth.models import User
from .models import ProfilUzytkownika

class UzytkownikForm(forms.ModelForm):
    password1 = forms.CharField(label='Hasło', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Potwierdź hasło', widget=forms.PasswordInput)
    telefon = forms.CharField(label='Telefon', required=False, max_length=20)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'is_staff', 'is_superuser']
        labels = {
            'first_name': 'Imię',
            'last_name': 'Nazwisko',
            'username': 'Login',
            'email': 'Email',
            'is_staff': 'Dostęp do panelu admina',
            'is_superuser': 'Administrator (pełne uprawnienia)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = False

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Hasła nie są identyczne.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
            ProfilUzytkownika.objects.create(
                user=user,
                telefon=self.cleaned_data.get('telefon')
            )
        return user