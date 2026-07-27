from django.db import migrations, models
import django.db.models.deletion


def przenies_oddzialy(apps, schema_editor):
    Pojazd = apps.get_model('pojazdy', 'Pojazd')
    Oddzial = apps.get_model('administracja', 'Oddzial')
    for pojazd in Pojazd.objects.exclude(oddzial__isnull=True).exclude(oddzial=''):
        oddzial, _ = Oddzial.objects.get_or_create(nazwa=pojazd.oddzial.strip())
        pojazd.oddzial_nowy = oddzial
        pojazd.save(update_fields=['oddzial_nowy'])


def cofnij_oddzialy(apps, schema_editor):
    Pojazd = apps.get_model('pojazdy', 'Pojazd')
    for pojazd in Pojazd.objects.exclude(oddzial_nowy__isnull=True):
        pojazd.oddzial = pojazd.oddzial_nowy.nazwa
        pojazd.save(update_fields=['oddzial'])


class Migration(migrations.Migration):

    dependencies = [
        ('administracja', '0003_oddzial'),
        ('pojazdy', '0010_pojazd_data_pierwszej_rejestracji_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='pojazd',
            name='oddzial_nowy',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pojazdy', to='administracja.oddzial', verbose_name='Oddział'),
        ),
        migrations.RunPython(przenies_oddzialy, cofnij_oddzialy),
        migrations.RemoveField(
            model_name='pojazd',
            name='oddzial',
        ),
        migrations.RenameField(
            model_name='pojazd',
            old_name='oddzial_nowy',
            new_name='oddzial',
        ),
    ]
