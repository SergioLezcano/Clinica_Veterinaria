from datetime import timedelta
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from gestion_veterinaria.models import HistoriaClinica
from ..models import Turno

logger = logging.getLogger(__name__)


class TurnoService:
    """
    Servicio encargado de la gestión integral de turnos médicos,
    agenda de citas, check-in a consultorio y notificaciones por correo electrónico.
    """

    @staticmethod
    def listar_turnos():
        return (
            Turno.objects
            .select_related("mascota", "mascota__dueño", "consulta")
            .order_by("-fecha_hora")
        )

    @staticmethod
    def obtener_turno(turno_id):
        return get_object_or_404(
            Turno.objects.select_related("mascota", "mascota__dueño", "consulta"),
            pk=turno_id
        )

    @staticmethod
    @transaction.atomic
    def crear_turno(form):
        """
        Guarda el turno y despacha la notificación automática por correo al dueño.
        """
        turno = form.save()

        # Intento de envío de confirmación por correo
        TurnoService.enviar_email_confirmacion(turno)

        return turno

    @staticmethod
    def enviar_email_confirmacion(turno):
        """
        Envía un correo HTML estilizado con el detalle del turno al dueño de la mascota.
        """
        dueño = turno.mascota.dueño
        email_destino = dueño.email

        if not email_destino:
            logger.warning("No se pudo enviar email de turno #%s: Dueño sin email", turno.id)
            return False

        asunto = f"Confirmación de Turno para {turno.mascota.nombre} - Clínica Veterinaria"
        contexto = {
            "turno": turno,
        }

        try:
            contenido_html = render_to_string("turnos/emails/confirmacion_turno.html", contexto)
            contenido_texto = strip_tags(contenido_html)

            mensaje = EmailMultiAlternatives(
                subject=asunto,
                body=contenido_texto,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email_destino],
            )
            mensaje.attach_alternative(contenido_html, "text/html")
            mensaje.send(fail_silently=False)

            turno.notificado_email = True
            turno.save(update_fields=["notificado_email"])
            logger.info("Email de confirmación de turno #%s enviado a %s", turno.id, email_destino)
            return True

        except Exception as e:
            logger.error("Error al enviar email de confirmación para turno #%s: %s", turno.id, str(e))
            return False

    @staticmethod
    def eventos_calendario(fecha_inicio=None, fecha_fin=None):
        """
        Devuelve la lista de eventos en formato JSON listo para FullCalendar.
        """
        queryset = (
            Turno.objects
            .select_related("mascota", "mascota__dueño", "consulta")
        )

        if fecha_inicio and fecha_fin:
            queryset = queryset.filter(fecha_hora__range=(fecha_inicio, fecha_fin))

        colores_por_estado = {
            Turno.Estado.PENDIENTE: {"bg": "#f59e0b", "border": "#d97706"},
            Turno.Estado.CONFIRMADO: {"bg": "#0ea5e9", "border": "#0284c7"},
            Turno.Estado.ATENDIDO: {"bg": "#10b981", "border": "#059669"},
            Turno.Estado.CANCELADO: {"bg": "#ef4444", "border": "#dc2626"},
        }

        eventos = []
        for turno in queryset:
            paleta = colores_por_estado.get(
                turno.estado,
                {"bg": "#64748b", "border": "#475569"}
            )

            # Duración estimada por defecto: 30 minutos
            fin_estimado = turno.fecha_hora + timedelta(minutes=30)

            eventos.append({
                "id": turno.id,
                "title": f"🐾 {turno.mascota.nombre} ({turno.mascota.dueño.apellido})",
                "start": turno.fecha_hora.isoformat(),
                "end": fin_estimado.isoformat(),
                "backgroundColor": paleta["bg"],
                "borderColor": paleta["border"],
                "textColor": "#ffffff",
                "extendedProps": {
                    "paciente": turno.mascota.nombre,
                    "especie": turno.mascota.especie,
                    "dueño": f"{turno.mascota.dueño.nombre} {turno.mascota.dueño.apellido}",
                    "telefono": turno.mascota.dueño.telefono,
                    "email": turno.mascota.dueño.email,
                    "motivo": turno.motivo,
                    "estado_codigo": turno.estado,
                    "estado_nombre": turno.get_estado_display(),
                    "notificado_email": turno.notificado_email,
                    "observaciones": turno.observaciones or "",
                    "consulta_id": turno.consulta_id,
                    "ingresado": bool(turno.consulta_id),
                }
            })

        return eventos

    @staticmethod
    @transaction.atomic
    def dar_ingreso_consultorio(turno_id):
        """
        Realiza el check-in del paciente con turno y lo deriva a la sala de espera del médico:
        1. Crea una HistoriaClinica (preconsulta) en estado 'P' (Pendiente).
        2. Asocia la consulta médica creada al Turno.
        3. Actualiza el estado del turno a 'ATENDIDO'.
        """
        turno = TurnoService.obtener_turno(turno_id)

        if turno.estado == Turno.Estado.CANCELADO:
            raise ValueError("No se puede dar ingreso a un turno que ha sido cancelado.")

        if turno.consulta:
            return turno.consulta, False

        motivo_consulta = f"[Turno Programado] {turno.motivo}"
        if turno.observaciones:
            motivo_consulta += f" (Obs: {turno.observaciones})"

        consulta = HistoriaClinica.objects.create(
            mascota=turno.mascota,
            motivo=motivo_consulta,
            estado='P'
        )

        turno.consulta = consulta
        turno.estado = Turno.Estado.ATENDIDO
        turno.save(update_fields=["consulta", "estado"])
        logger.info("Turno #%s ingresado a Sala de Espera como Consulta #%s", turno.id, consulta.id)
        return consulta, True

    @staticmethod
    @transaction.atomic
    def cancelar_turno(turno_id):
        turno = TurnoService.obtener_turno(turno_id)
        turno.estado = Turno.Estado.CANCELADO
        turno.save(update_fields=["estado"])
        return turno

    @staticmethod
    @transaction.atomic
    def cambiar_estado(turno_id, nuevo_estado):
        turno = TurnoService.obtener_turno(turno_id)
        if nuevo_estado in Turno.Estado.values:
            turno.estado = nuevo_estado
            turno.save(update_fields=["estado"])
        return turno
