from django.conf import settings
from django.db import models


class Perfil(models.Model):

    class Rol(models.TextChoices):
        PACIENTE = 'PACIENTE', 'Paciente'
        ADMINISTRATIVO = 'ADMINISTRATIVO', 'Personal administrativo'
        MEDICO = 'MEDICO', 'Profesional de salud'

    class Prevision(models.TextChoices):
        FONASA = 'FONASA', 'Fonasa'
        ISAPRE = 'ISAPRE', 'Isapre'
        PARTICULAR = 'PARTICULAR', 'Particular (sin previsión)'

    COBERTURA = {'FONASA': 60, 'ISAPRE': 70, 'PARTICULAR': 0}

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil')
    rut = models.CharField('RUT', max_length=12, unique=True)
    telefono = models.CharField('Teléfono', max_length=20, blank=True)
    rol = models.CharField('Rol institucional', max_length=15, choices=Rol.choices, default=Rol.PACIENTE)
    prevision = models.CharField(
        'Previsión', max_length=12, choices=Prevision.choices, default=Prevision.PARTICULAR)

    class Meta:
        verbose_name = 'Perfil de usuario'
        verbose_name_plural = 'Perfiles de usuario'

    def __str__(self):
        return f'{self.usuario.get_username()} ({self.get_rol_display()})'
