from django.contrib import admin

from .models import ProfilUzytkownika, UkladTabeli

admin.site.register(ProfilUzytkownika)


@admin.register(UkladTabeli)
class UkladTabeliAdmin(admin.ModelAdmin):
    list_display = ('user', 'tabela', 'nazwa', 'aktywny')
    list_filter = ('tabela', 'aktywny')
