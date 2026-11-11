from django.contrib.auth.models import User
from django.core.management import call_command
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse

from cuentas.models import Perfil

from .models import Especialidad, Prestacion


class BaseTest(TestCase):
    def setUp(self):
        self.esp = Especialidad.objects.create(nombre='Lab')
        self.p1 = Prestacion.objects.create(
            especialidad=self.esp, codigo='L1', nombre='Hemograma', descripcion='x', arancel=10000, cupos_diarios=3)
        self.p2 = Prestacion.objects.create(
            especialidad=self.esp, codigo='L2', nombre='Glicemia', descripcion='y', arancel=5000, cupos_diarios=0)
        self.staff = User.objects.create_user('staff', password='x12345678', is_staff=True)
        self.pac = User.objects.create_user('pac', password='x12345678')
        Perfil.objects.create(usuario=self.pac, rut='33333333-3', prevision='FONASA')


class ModeloTests(BaseTest):
    def test_protect(self):
        with self.assertRaises(ProtectedError):
            self.esp.delete()

    def test_slug_automatico(self):
        self.assertTrue(self.p1.slug)

    def test_poblar_datos(self):
        call_command('poblar_datos', verbosity=0)
        self.assertGreaterEqual(Especialidad.objects.count(), 4)
        self.assertGreaterEqual(Prestacion.objects.count(), 8)


class CatalogoTests(BaseTest):
    def test_busqueda_y_filtro(self):
        r = self.client.get(reverse('catalogo:lista'), {'q': 'hemo'})
        self.assertContains(r, 'Hemograma')
        self.assertNotContains(r, 'Glicemia')

    def test_baja_logica_oculta(self):
        self.client.login(username='staff', password='x12345678')
        self.client.post(reverse('catalogo:eliminar', args=[self.p1.pk]))
        self.p1.refresh_from_db()
        self.assertFalse(self.p1.activo)
        self.assertNotContains(self.client.get(reverse('catalogo:lista')), self.p1.get_absolute_url())

    def test_rutas_protegidas(self):
        for name in ('catalogo:gestion', 'catalogo:crear'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 302)
        self.client.login(username='pac', password='x12345678')
        self.assertEqual(self.client.get(reverse('catalogo:gestion')).status_code, 302)
        self.client.login(username='staff', password='x12345678')
        self.assertEqual(self.client.get(reverse('catalogo:gestion')).status_code, 200)

    def test_codigo_duplicado(self):
        self.client.login(username='staff', password='x12345678')
        r = self.client.post(reverse('catalogo:crear'), {
            'especialidad': self.esp.pk, 'codigo': 'l1', 'nombre': 'N', 'descripcion': 'd',
            'arancel': 100, 'duracion_minutos': 10, 'cupos_diarios': 1, 'estado': 'DISPONIBLE', 'activo': 'on'})
        self.assertContains(r, 'Ya existe una prestación')


class CanastaTests(BaseTest):
    def test_agregar_y_cupos(self):
        self.client.post(reverse('catalogo:canasta_agregar', args=[self.p1.pk]), {'cantidad': 2})
        self.assertEqual(self.client.session['canasta'], {str(self.p1.pk): 2})
        # Excede cupos (3)
        self.client.post(reverse('catalogo:canasta_agregar', args=[self.p1.pk]), {'cantidad': 2})
        self.assertEqual(self.client.session['canasta'][str(self.p1.pk)], 2)
        # Sin cupos
        self.client.post(reverse('catalogo:canasta_agregar', args=[self.p2.pk]))
        self.assertNotIn(str(self.p2.pk), self.client.session['canasta'])

    def test_totales_y_contexto(self):
        self.client.post(reverse('catalogo:canasta_agregar', args=[self.p1.pk]), {'cantidad': 2})
        self.client.post(reverse('catalogo:canasta_prevision'), {'prevision': 'FONASA'})
        r = self.client.get(reverse('catalogo:canasta'))
        self.assertEqual(r.context['canasta_cantidad'], 2)
        self.assertEqual(r.context['c']['subtotal'], 20000)
        self.assertEqual(r.context['c']['copago_total'], 8000)

    def test_modificar_quitar_vaciar(self):
        url = reverse('catalogo:canasta_agregar', args=[self.p1.pk])
        self.client.post(url)
        self.client.post(reverse('catalogo:canasta_modificar', args=[self.p1.pk]), {'cantidad': 3})
        self.assertEqual(self.client.session['canasta'][str(self.p1.pk)], 3)
        self.client.post(reverse('catalogo:canasta_quitar', args=[self.p1.pk]))
        self.assertEqual(self.client.session['canasta'], {})
        self.client.post(url)
        self.client.post(reverse('catalogo:canasta_vaciar'))
        self.assertNotIn('canasta', self.client.session)

    def test_confirmar_requiere_login_y_vacia(self):
        self.client.post(reverse('catalogo:canasta_agregar', args=[self.p1.pk]))
        r = self.client.post(reverse('catalogo:canasta_confirmar'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('canasta', self.client.session)
        self.client.login(username='pac', password='x12345678')
        # el login rota la sesión conservando datos
        r = self.client.post(reverse('catalogo:canasta_confirmar'))
        self.assertContains(r, 'Comprobante simulado')
        self.assertNotIn('canasta', self.client.session)


class CuentasTests(TestCase):
    def test_registro_y_logout(self):
        r = self.client.post(reverse('cuentas:registro'), {
            'username': 'nuevo', 'first_name': 'A', 'last_name': 'B', 'email': 'a@b.cl',
            'rut': '12.345.678-5', 'telefono': '', 'prevision': 'ISAPRE',
            'password1': 'Clave-Segura-9', 'password2': 'Clave-Segura-9'})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Perfil.objects.get(usuario__username='nuevo').rut, '12345678-5')
        self.client.post(reverse('cuentas:logout'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_rut_invalido(self):
        r = self.client.post(reverse('cuentas:registro'), {
            'username': 'n2', 'first_name': 'A', 'last_name': 'B', 'email': 'c@d.cl',
            'rut': '12345678-9', 'prevision': 'FONASA',
            'password1': 'Clave-Segura-9', 'password2': 'Clave-Segura-9'})
        self.assertContains(r, 'dígito verificador')
