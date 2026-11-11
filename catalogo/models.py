from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Especialidad(models.Model):
    """Entidad de contexto: clasifica las prestaciones (Cardiología, etc.)."""
    nombre = models.CharField('Nombre', max_length=80, unique=True)
    descripcion = models.TextField('Descripción', blank=True)
    icono = models.CharField(
        'Ícono Bootstrap', max_length=40, default='bi-heart-pulse',
        help_text='Clase de Bootstrap Icons, ej.: bi-heart-pulse')
    activa = models.BooleanField('Vigente', default=True)

    class Meta:
        verbose_name = 'Especialidad médica'
        verbose_name_plural = 'Especialidades médicas'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Prestacion(models.Model):
    """Entidad principal gestionable: examen o prestación clínica."""

    class Estado(models.TextChoices):
        DISPONIBLE = 'DISPONIBLE', 'Disponible'
        SUSPENDIDA = 'SUSPENDIDA', 'Suspendida'
        AGOTADA = 'AGOTADA', 'Sin cupos'
        MANTENCION = 'MANTENCION', 'En mantención de equipo'

    especialidad = models.ForeignKey(
        Especialidad, on_delete=models.PROTECT,
        related_name='prestaciones', verbose_name='Especialidad')
    codigo = models.CharField('Código', max_length=20, unique=True)
    slug = models.SlugField('Slug', max_length=120, unique=True, blank=True)
    nombre = models.CharField('Nombre de la prestación', max_length=150)
    descripcion = models.TextField('Descripción')
    requisitos = models.TextField('Requisitos previos', blank=True)
    arancel = models.DecimalField(
        'Arancel (CLP)', max_digits=10, decimal_places=0,
        validators=[MinValueValidator(Decimal('0'))])
    duracion_minutos = models.PositiveIntegerField(
        'Duración (min)', default=30, validators=[MinValueValidator(1)])
    cupos_diarios = models.PositiveIntegerField(
        'Cupos disponibles', default=10, validators=[MinValueValidator(0)])
    estado = models.CharField(
        'Estado', max_length=12, choices=Estado.choices, default=Estado.DISPONIBLE)
    imagen = models.ImageField('Imagen', upload_to='prestaciones/', blank=True, null=True)
    # Baja lógica: permite desactivar sin borrar físicamente.
    activo = models.BooleanField('Vigente', default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Prestación'
        verbose_name_plural = 'Prestaciones'
        ordering = ['especialidad__nombre', 'nombre']

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f'{self.codigo}-{self.nombre}')[:120]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('catalogo:detalle', args=[self.slug])

    @property
    def reservable(self):
        """Se puede agregar a la canasta solo si está vigente, disponible y con cupos."""
        return self.activo and self.estado == self.Estado.DISPONIBLE and self.cupos_diarios > 0
