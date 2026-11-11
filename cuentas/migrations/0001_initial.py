from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Perfil',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rut', models.CharField(max_length=12, unique=True, verbose_name='RUT')),
                ('telefono', models.CharField(blank=True, max_length=20, verbose_name='Teléfono')),
                ('rol', models.CharField(choices=[('PACIENTE', 'Paciente'), ('ADMINISTRATIVO', 'Personal administrativo'), ('MEDICO', 'Profesional de salud')], default='PACIENTE', max_length=15, verbose_name='Rol institucional')),
                ('prevision', models.CharField(choices=[('FONASA', 'Fonasa'), ('ISAPRE', 'Isapre'), ('PARTICULAR', 'Particular (sin previsión)')], default='PARTICULAR', max_length=12, verbose_name='Previsión')),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='perfil', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Perfil de usuario',
                'verbose_name_plural': 'Perfiles de usuario',
            },
        ),
    ]
