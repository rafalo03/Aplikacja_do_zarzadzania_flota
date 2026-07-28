from django.contrib import admin
from .models import Cennik, PozycjaCennika, Rezerwacja, ZmianaPojazdu

class PozycjaCennikаInline(admin.TabularInline):
    model = PozycjaCennika
    extra = 1

@admin.register(Cennik)
class CennikAdmin(admin.ModelAdmin):
    inlines = [PozycjaCennikаInline]

class ZmianaPojazduInline(admin.TabularInline):
    model = ZmianaPojazdu
    extra = 1

@admin.register(Rezerwacja)
class RezerwacjaAdmin(admin.ModelAdmin):
    inlines = [ZmianaPojazduInline]