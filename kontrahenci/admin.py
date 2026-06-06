from django.contrib import admin
from .models import Kontrahent, DodatkoweDaneKontaktowe

class DodatkoweDaneInline(admin.TabularInline):
    model = DodatkoweDaneKontaktowe
    extra = 1

@admin.register(Kontrahent)
class KontrahentAdmin(admin.ModelAdmin):
    inlines = [DodatkoweDaneInline]

admin.site.register(DodatkoweDaneKontaktowe)