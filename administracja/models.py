from django.db import models
from django.contrib.auth.models import User

class ProfilUzytkownika(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil')
    telefon = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"Profil {self.user.get_full_name()}"

    class Meta:
        verbose_name = 'Profil użytkownika'
        verbose_name_plural = 'Profile użytkowników'