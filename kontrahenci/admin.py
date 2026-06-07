from django.contrib import admin
from .models import Kontrahent, DodatkoweDaneKontaktowe, UzytkownikPojazdu
admin.site.register(UzytkownikPojazdu)

class DodatkoweDaneInline(admin.TabularInline):
    model = DodatkoweDaneKontaktowe
    extra = 1

@admin.register(Kontrahent)
class KontrahentAdmin(admin.ModelAdmin):
    inlines = [DodatkoweDaneInline]

admin.site.register(DodatkoweDaneKontaktowe)