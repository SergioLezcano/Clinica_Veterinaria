from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from .models import PerfilUsuario
from .services.usuario_service import UsuarioService


class OperadorAltaYConfirmacionEmailTests(TestCase):

    def setUp(self):
        # Crear usuario administrador para autenticarse
        self.admin_user = User.objects.create_superuser(
            username='admin_veterinario',
            email='admin@veterinaria.com',
            password='adminpassword123'
        )
        PerfilUsuario.objects.create(
            user=self.admin_user,
            rol=PerfilUsuario.Rol.ADMINISTRADOR
        )

    def test_alta_operador_crea_usuario_y_envia_correo(self):
        """Verifica que el alta de un nuevo operador envíe el email con el enlace de confirmación."""
        self.client.login(username='admin_veterinario', password='adminpassword123')

        url_alta = reverse('alta_operador')
        post_data = {
            'username': 'lucas_operador',
            'first_name': 'Lucas',
            'last_name': 'Perez',
            'email': 'lucas@example.com',
            'password': '',
            'confirmar_password': '',
        }

        response = self.client.post(url_alta, data=post_data)
        self.assertRedirects(response, reverse('gestion_operadores'))

        # 1. Verificar que el usuario y perfil se crearon en la BD
        self.assertTrue(User.objects.filter(username='lucas_operador').exists())
        user_creado = User.objects.get(username='lucas_operador')
        self.assertEqual(user_creado.email, 'lucas@example.com')
        self.assertEqual(user_creado.perfilusuario.rol, PerfilUsuario.Rol.OPERADOR)

        # 2. Verificar que se envió exactamente un correo electrónico
        self.assertEqual(len(mail.outbox), 1)
        email_enviado = mail.outbox[0]
        self.assertEqual(email_enviado.to, ['lucas@example.com'])
        self.assertIn('Bienvenido a Clínica Veterinaria', email_enviado.subject)
        self.assertIn('lucas_operador', email_enviado.body)
        self.assertIn('establecer-password', email_enviado.body)

    def test_establecer_password_con_token_valido(self):
        """Verifica que el operador pueda acceder con el token del email y configurar su contraseña."""
        # 1. Crear operador sin contraseña conocida
        user = User.objects.create_user(
            username='marcos_operador',
            first_name='Marcos',
            email='marcos@example.com'
        )
        PerfilUsuario.objects.create(user=user, rol=PerfilUsuario.Rol.OPERADOR)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        url_establecer = reverse(
            'establecer_password_operador',
            kwargs={'uidb64': uid, 'token': token}
        )

        # 2. Acceder al enlace vía GET (público, sin necesidad de login)
        get_response = self.client.get(url_establecer)
        self.assertEqual(get_response.status_code, 200)
        self.assertTemplateUsed(get_response, 'gestion/establecer_password.html')
        self.assertContains(get_response, 'marcos_operador')

        # 3. Enviar nueva contraseña válida
        nueva_clave = 'ClaveSegura2026!'
        post_response = self.client.post(url_establecer, data={
            'new_password1': nueva_clave,
            'new_password2': nueva_clave,
        })

        # Debe redirigir al login
        self.assertRedirects(post_response, reverse('login'))

        # 4. Verificar que la nueva contraseña quedó registrada en la BD y puede autenticarse
        user_auth = authenticate(username='marcos_operador', password=nueva_clave)
        self.assertIsNotNone(user_auth)
        self.assertTrue(user_auth.is_active)

    def test_token_invalido_o_reutilizado_muestra_error(self):
        """Verifica que un token alterado o reutilizado después de cambiar la contraseña sea rechazado."""
        user = User.objects.create_user(
            username='ana_operador',
            email='ana@example.com',
            password='password1'
        )
        PerfilUsuario.objects.create(user=user, rol=PerfilUsuario.Rol.OPERADOR)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # Cambiamos la contraseña para invalidar el token anterior
        user.set_password('password2_cambiada')
        user.save()

        url_establecer = reverse(
            'establecer_password_operador',
            kwargs={'uidb64': uid, 'token': token}
        )

        response = self.client.get(url_establecer)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gestion/password_token_invalido.html')
        self.assertContains(response, 'Enlace No Válido o Expirado')

    def test_reenviar_confirmacion_operador(self):
        """Verifica que el administrador pueda reenviar el correo de confirmación."""
        self.client.login(username='admin_veterinario', password='adminpassword123')

        user = User.objects.create_user(
            username='franco_operador',
            email='franco@example.com'
        )
        PerfilUsuario.objects.create(user=user, rol=PerfilUsuario.Rol.OPERADOR)

        url_reenviar = reverse('reenviar_confirmacion_operador', kwargs={'pk': user.id})
        response = self.client.post(url_reenviar)
        self.assertRedirects(response, reverse('gestion_operadores'))

        # Verificar que se envió el correo a franco@example.com
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['franco@example.com'])
        self.assertIn('franco_operador', mail.outbox[0].body)
