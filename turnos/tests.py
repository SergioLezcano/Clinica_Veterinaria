from datetime import timedelta
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from gestion_veterinaria.models import Dueño, Mascota, PerfilUsuario, HistoriaClinica
from turnos.forms import TurnoForm
from turnos.models import Turno
from turnos.services.turno_service import TurnoService


class TurnosTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='recepcionista',
            password='testpassword123'
        )
        PerfilUsuario.objects.create(
            user=self.user,
            rol=PerfilUsuario.Rol.OPERADOR
        )
        self.admin_user = User.objects.create_superuser(
            username='doctor_admin',
            email='admin@veterinaria.com',
            password='adminpassword123'
        )
        PerfilUsuario.objects.create(
            user=self.admin_user,
            rol=PerfilUsuario.Rol.ADMINISTRADOR
        )
        self.dueño = Dueño.objects.create(
            nombre='Carlos',
            apellido='Gomez',
            telefono='1122334455',
            email='carlos.gomez@example.com'
        )
        self.mascota = Mascota.objects.create(
            dueño=self.dueño,
            nombre='Toby',
            especie='Perro',
            raza='Labrador',
            sexo=Mascota.Sexo.MACHO
        )
        self.fecha_futura = timezone.now() + timedelta(days=2)

    def test_crear_turno_y_envio_correo(self):
        """Verifica que al guardar un turno se intente enviar el correo y se marque notificado_email."""
        form_data = {
            'mascota': self.mascota.id,
            'fecha_hora': self.fecha_futura.strftime('%Y-%m-%dT%H:%M'),
            'motivo': 'Vacunación Séxtuple y desparasitación.',
            'estado': Turno.Estado.CONFIRMADO,
            'observaciones': 'Venir en ayunas de sólidos.'
        }
        form = TurnoForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

        turno = TurnoService.crear_turno(form)
        self.assertIsNotNone(turno.pk)
        self.assertEqual(turno.estado, Turno.Estado.CONFIRMADO)
        self.assertTrue(turno.notificado_email)

        # Verificar correo en outbox de Django
        self.assertEqual(len(mail.outbox), 1)
        email_enviado = mail.outbox[0]
        self.assertIn("Toby", email_enviado.subject)
        self.assertEqual(email_enviado.to, ['carlos.gomez@example.com'])
        self.assertIn("Vacunación Séxtuple", email_enviado.body)

    def test_turno_validacion_fecha_pasada(self):
        """Verifica que el formulario rechace turnos en el pasado."""
        fecha_pasada = timezone.now() - timedelta(days=1)
        form_data = {
            'mascota': self.mascota.id,
            'fecha_hora': fecha_pasada.strftime('%Y-%m-%dT%H:%M'),
            'motivo': 'Control rutinario',
            'estado': Turno.Estado.PENDIENTE,
        }
        form = TurnoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_hora', form.errors)

    def test_eventos_calendario_json(self):
        """Verifica que el servicio arme los eventos de FullCalendar correctamente."""
        Turno.objects.create(
            mascota=self.mascota,
            fecha_hora=self.fecha_futura,
            motivo='Control de piel',
            estado=Turno.Estado.PENDIENTE
        )
        eventos = TurnoService.eventos_calendario()
        self.assertEqual(len(eventos), 1)
        evento = eventos[0]
        self.assertIn('Toby', evento['title'])
        self.assertEqual(evento['extendedProps']['paciente'], 'Toby')
        self.assertEqual(evento['extendedProps']['dueño'], 'Carlos Gomez')
        self.assertEqual(evento['extendedProps']['email'], 'carlos.gomez@example.com')

    def test_cancelar_y_cambiar_estado(self):
        """Verifica la transición de estados en un turno."""
        turno = Turno.objects.create(
            mascota=self.mascota,
            fecha_hora=self.fecha_futura,
            motivo='Cirugía menor',
            estado=Turno.Estado.PENDIENTE
        )
        TurnoService.cambiar_estado(turno.id, Turno.Estado.CONFIRMADO)
        turno.refresh_from_db()
        self.assertEqual(turno.estado, Turno.Estado.CONFIRMADO)

        TurnoService.cancelar_turno(turno.id)
        turno.refresh_from_db()
        self.assertEqual(turno.estado, Turno.Estado.CANCELADO)

    def test_vistas_calendario_y_api(self):
        """Verifica las vistas con usuario autenticado."""
        self.client.login(username='recepcionista', password='testpassword123')

        # Vista del calendario principal
        response = self.client.get(reverse('calendario_turnos'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'turnos/calendario.html')

        # API de eventos para FullCalendar
        response_api = self.client.get(reverse('api_eventos_turnos'))
        self.assertEqual(response_api.status_code, 200)
        self.assertEqual(response_api['Content-Type'], 'application/json')

    def test_navegacion_rol_operador(self):
        """Verifica que el operador vea su rol y el enlace de retorno al menu de operador."""
        self.client.login(username='recepcionista', password='testpassword123')
        response = self.client.get(reverse('calendario_turnos'))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['es_admin'])
        self.assertEqual(response.context['url_volver'], 'menu_operador')

        contenido = response.content.decode('utf-8')
        self.assertIn("Operador:", contenido)
        self.assertIn("Área Administrativa", contenido)
        self.assertIn(reverse('menu_operador'), contenido)
        self.assertNotIn(reverse('menu_administrador'), contenido)

    def test_navegacion_rol_administrador(self):
        """Verifica que el administrador médico vea su rol y el enlace de retorno al menu de administrador."""
        self.client.login(username='doctor_admin', password='adminpassword123')
        response = self.client.get(reverse('calendario_turnos'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['es_admin'])
        self.assertEqual(response.context['url_volver'], 'menu_administrador')

        contenido = response.content.decode('utf-8')
        self.assertIn("Médico:", contenido)
        self.assertIn("Administrador", contenido)
        self.assertIn(reverse('menu_administrador'), contenido)
        self.assertNotIn(reverse('menu_operador'), contenido)

    def test_checkin_ingreso_a_sala_de_espera(self):
        """Verifica que el servicio cree la HistoriaClinica en 'P' y marque el turno como ATENDIDO."""
        turno = Turno.objects.create(
            mascota=self.mascota,
            fecha_hora=self.fecha_futura,
            motivo='Vacunación antirrábica obligatoria',
            observaciones='Traer carnet',
            estado=Turno.Estado.CONFIRMADO
        )

        consulta, creado = TurnoService.dar_ingreso_consultorio(turno.id)
        self.assertTrue(creado)
        self.assertIsNotNone(consulta.pk)
        self.assertEqual(consulta.mascota, self.mascota)
        self.assertEqual(consulta.estado, 'P')
        self.assertIn("Vacunación antirrábica", consulta.motivo)

        turno.refresh_from_db()
        self.assertEqual(turno.estado, Turno.Estado.ATENDIDO)
        self.assertEqual(turno.consulta, consulta)

        # Si se llama de nuevo, no debe duplicar la consulta
        consulta_2, creado_2 = TurnoService.dar_ingreso_consultorio(turno.id)
        self.assertFalse(creado_2)
        self.assertEqual(consulta_2.pk, consulta.pk)

    def test_ingresar_sala_espera_view_ajax(self):
        """Verifica el endpoint de check-in vía AJAX desde el calendario."""
        self.client.login(username='recepcionista', password='testpassword123')
        turno = Turno.objects.create(
            mascota=self.mascota,
            fecha_hora=self.fecha_futura,
            motivo='Control clínico',
            estado=Turno.Estado.CONFIRMADO
        )

        url = reverse('ingresar_sala_espera', kwargs={'pk': turno.id})
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertIn('ingresado a la Sala de Espera', data['mensaje'])

        # Verificar que la consulta existe en la BD
        self.assertTrue(HistoriaClinica.objects.filter(mascota=self.mascota, estado='P').exists())

