import io

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image, ImageDraw

from catalogo.models import Especialidad, Prestacion
from cuentas.models import Perfil

ESPECIALIDADES = [
    ('Cardiología', 'Diagnóstico y control de enfermedades del corazón.', 'bi-heart-pulse', (192, 57, 43)),
    ('Laboratorio Clínico', 'Exámenes de sangre, orina y otras muestras.', 'bi-droplet', (41, 128, 185)),
    ('Imagenología', 'Radiografías, ecografías y otros estudios por imágenes.', 'bi-camera', (39, 174, 96)),
    ('Oftalmología', 'Evaluación y cuidado de la salud visual.', 'bi-eye', (142, 68, 173)),
    ('Nutrición', 'Evaluación nutricional y planes alimentarios.', 'bi-apple', (230, 126, 34)),
]

# (código, especialidad, nombre, descripción, requisitos, arancel, minutos, cupos, estado)
PRESTACIONES = [
    ('CAR-001', 'Cardiología', 'Electrocardiograma de reposo', 'Registro de la actividad eléctrica del corazón en reposo.', 'Evitar cremas en el pecho el día del examen.', 25000, 20, 12, 'DISPONIBLE'),
    ('CAR-002', 'Cardiología', 'Test de esfuerzo', 'Evaluación de la respuesta cardíaca durante ejercicio controlado.', 'Ropa cómoda, ayuno de 3 horas. Traer zapatillas.', 68000, 45, 5, 'DISPONIBLE'),
    ('LAB-001', 'Laboratorio Clínico', 'Hemograma completo', 'Recuento de glóbulos rojos, blancos y plaquetas.', 'Ayuno de 8 horas.', 8500, 10, 30, 'DISPONIBLE'),
    ('LAB-002', 'Laboratorio Clínico', 'Perfil lipídico', 'Colesterol total, HDL, LDL y triglicéridos.', 'Ayuno de 12 horas.', 14500, 10, 25, 'DISPONIBLE'),
    ('LAB-003', 'Laboratorio Clínico', 'Glicemia en ayunas', 'Medición de glucosa en sangre.', 'Ayuno de 8 horas.', 4500, 10, 40, 'DISPONIBLE'),
    ('IMG-001', 'Imagenología', 'Radiografía de tórax', 'Imagen de pulmones, corazón y estructuras del tórax.', 'Informar si hay embarazo.', 22000, 15, 15, 'DISPONIBLE'),
    ('IMG-002', 'Imagenología', 'Ecografía abdominal', 'Estudio por ultrasonido de órganos abdominales.', 'Ayuno de 6 horas y vejiga llena.', 42000, 30, 8, 'DISPONIBLE'),
    ('IMG-003', 'Imagenología', 'Resonancia magnética de rodilla', 'Estudio detallado de articulación de la rodilla.', 'Retirar objetos metálicos. Informar implantes.', 185000, 50, 0, 'MANTENCION'),
    ('OFT-001', 'Oftalmología', 'Fondo de ojo', 'Examen de retina y nervio óptico.', 'Venir con acompañante (dilatación pupilar).', 30000, 25, 10, 'DISPONIBLE'),
    ('OFT-002', 'Oftalmología', 'Control de presión intraocular', 'Tonometría para detección de glaucoma.', '', 18000, 15, 14, 'DISPONIBLE'),
    ('NUT-001', 'Nutrición', 'Evaluación nutricional inicial', 'Antropometría, anamnesis alimentaria y plan inicial.', 'Traer exámenes recientes si los tiene.', 27000, 40, 9, 'DISPONIBLE'),
    ('NUT-002', 'Nutrición', 'Control nutricional de seguimiento', 'Seguimiento y ajuste del plan alimentario.', '', 19000, 30, 0, 'SUSPENDIDA'),
]


def _imagen(titulo, color):
    """Genera una imagen ilustrativa con Pillow (no requiere archivos externos)."""
    img = Image.new('RGB', (600, 400), color)
    d = ImageDraw.Draw(img)
    d.ellipse((220, 90, 380, 250), outline='white', width=8)
    d.line((300, 130, 300, 210), fill='white', width=10)
    d.line((260, 170, 340, 170), fill='white', width=10)
    d.text((24, 340), titulo[:50], fill='white')
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    return ContentFile(buf.getvalue())


class Command(BaseCommand):
    help = 'Carga datos iniciales coherentes con un centro médico (especialidades, prestaciones y usuarios de prueba).'

    @transaction.atomic
    def handle(self, *args, **options):
        colores, esp = {}, {}
        for nombre, desc, icono, color in ESPECIALIDADES:
            obj, _ = Especialidad.objects.get_or_create(
                nombre=nombre, defaults={'descripcion': desc, 'icono': icono})
            esp[nombre] = obj
            colores[nombre] = color

        creadas = 0
        for cod, enombre, nombre, desc, req, arancel, mins, cupos, estado in PRESTACIONES:
            p, nueva = Prestacion.objects.get_or_create(codigo=cod, defaults={
                'especialidad': esp[enombre], 'nombre': nombre, 'descripcion': desc,
                'requisitos': req, 'arancel': arancel, 'duracion_minutos': mins,
                'cupos_diarios': cupos, 'estado': estado})
            if nueva:
                p.imagen.save(f'{cod.lower()}.jpg', _imagen(nombre, colores[enombre]), save=True)
                creadas += 1

        # Usuarios de prueba
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                'admin', 'admin@saludvital.cl', 'Admin12345!', first_name='Administrador', last_name='SaludVital')
            Perfil.objects.create(usuario=admin, rut='11111111-1', telefono='+56911111111',
                                  rol=Perfil.Rol.ADMINISTRATIVO, prevision=Perfil.Prevision.PARTICULAR)
        if not User.objects.filter(username='paciente').exists():
            pac = User.objects.create_user(
                'paciente', 'paciente@saludvital.cl', 'Paciente12345!', first_name='Paula', last_name='Pérez')
            Perfil.objects.create(usuario=pac, rut='22222222-2', telefono='+56922222222',
                                  rol=Perfil.Rol.PACIENTE, prevision=Perfil.Prevision.FONASA)

        self.stdout.write(self.style.SUCCESS(
            f'Datos cargados: {Especialidad.objects.count()} especialidades, '
            f'{Prestacion.objects.count()} prestaciones ({creadas} nuevas).'))
        self.stdout.write('Usuarios: admin / Admin12345!  |  paciente / Paciente12345!')
