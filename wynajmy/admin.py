from django.contrib import admin
from .models import UzytkownikPojazdu, KlasaPojazdu, Cennik, PozycjaCennika, Rezerwacja

class PozycjaCennikаInline(admin.TabularInline):
    model = PozycjaCennika
    extra = 1

@admin.register(Cennik)
class CennikAdmin(admin.ModelAdmin):
    inlines = [PozycjaCennikаInline]

admin.site.register(UzytkownikPojazdu)
admin.site.register(Rezerwacja)