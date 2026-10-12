import logging
import secrets

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode

from ..models import PerfilUsuario

logger = logging.getLogger(__name__)


class UsuarioService:
    """
    Servicio encargado de la gestión de usuarios operadores.
    """
    @staticmethod
    def obtener_operadores():

        return (
            PerfilUsuario.objects
            .select_related("user")
            .filter(
                rol__in=[
                    "OPER",
                    "OPERADOR",
                    "OPERER"
                ]
            )
            .order_by("user__username")
        )

    @staticmethod
    @transaction.atomic
    def crear_operador(form, request=None):

        usuario = form.save(commit=False)

        password = form.cleaned_data.get("password")
        if password:
            usuario.set_password(password)
        else:
            usuario.set_password(secrets.token_urlsafe(16))

        usuario.save()

        PerfilUsuario.objects.create(
            user=usuario,
            rol="OPER"
        )

        enviado = UsuarioService.enviar_email_confirmacion_alta(usuario, request=request)

        return usuario, enviado

    @staticmethod
    def enviar_email_confirmacion_alta(usuario, request=None):
        """
        Envía un correo HTML estilizado al nuevo operador con un token
        seguro para que establezca o cambie su contraseña y complete su registro.
        """
        email_destino = usuario.email
        if not email_destino:
            logger.warning("No se pudo enviar email de alta a usuario #%s: Sin email", usuario.id)
            return False

        uid = urlsafe_base64_encode(force_bytes(usuario.pk))
        token = default_token_generator.make_token(usuario)

        relative_url = reverse(
            "establecer_password_operador",
            kwargs={"uidb64": uid, "token": token}
        )

        if request:
            link_activacion = request.build_absolute_uri(relative_url)
        else:
            link_activacion = relative_url

        asunto = f"Bienvenido a Clínica Veterinaria - Confirmación de Cuenta ({usuario.username})"
        contexto = {
            "usuario": usuario,
            "link_activacion": link_activacion,
        }

        try:
            contenido_html = render_to_string("gestion/emails/confirmacion_alta_operador.html", contexto)
            contenido_texto = strip_tags(contenido_html)

            mensaje = EmailMultiAlternatives(
                subject=asunto,
                body=contenido_texto,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email_destino],
            )
            mensaje.attach_alternative(contenido_html, "text/html")
            mensaje.send(fail_silently=False)

            logger.info("Email de confirmación de alta enviado a %s para usuario %s", email_destino, usuario.username)
            return True

        except Exception as e:
            logger.error("Error al enviar email de confirmación a %s: %s", email_destino, str(e))
            return False
    
    @staticmethod
    def obtener_usuario(usuario_id):

        return get_object_or_404(
            User,
            pk=usuario_id
        )
    
    @staticmethod
    @transaction.atomic
    def cambiar_estado(usuario_id):

        usuario = UsuarioService.obtener_usuario(
            usuario_id
        )

        if usuario.is_superuser:
            return usuario

        usuario.is_active = not usuario.is_active

        usuario.save(
            update_fields=["is_active"]
        )

        return usuario