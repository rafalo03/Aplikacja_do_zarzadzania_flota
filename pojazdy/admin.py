from django.contrib import admin
from .models import Marka, ModelPojazdu, Konfiguracja, Pojazd, Polisa

admin.site.register(Marka)
admin.site.register(ModelPojazdu)
admin.site.register(Konfiguracja)
admin.site.register(Pojazd)
admin.site.register(Polisa)