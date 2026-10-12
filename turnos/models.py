from django.db import models
from gestion_veterinaria.models import Mascota, HistoriaClinica


class Turno(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'PEN', 'Pendiente'
        CONFIRMADO = 'CONF', 'Confirmado'
        CANCELADO = 'CANC', 'Cancelado'
        ATENDIDO = 'ATEN', 'Atendido'

    mascota = models.ForeignKey(
        Mascota,
        on_delete=models.CASCADE,
        related_name='turnos'
    )
    consulta = models.OneToOneField(
        HistoriaClinica,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='turno_origen',
        help_text="Consulta médica generada en la sala de espera al hacer el check-in"
    )
    fecha_hora = models.DateTimeField(
        help_text="Fecha y hora de la cita"
    )
    motivo = models.TextField(
        help_text="Motivo de la consulta o procedimiento"
    )
    estado = models.CharField(
        max_length=4,
        choices=Estado.choices,
        default=Estado.PENDIENTE
    )
    notificado_email = models.BooleanField(
        default=False,
        help_text="Indica si se notificó al dueño por correo electrónico"
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        help_text="Notas adicionales para la recepción o el médico"
    )
    creado_el = models.DateTimeField(auto_now_add=True)
    actualizado_el = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['fecha_hora']
        verbose_name = 'Turno'
        verbose_name_plural = 'Turnos'

    def __str__(self):
        return f"Turno #{self.pk} - {self.mascota.nombre} ({self.fecha_hora.strftime('%d/%m/%Y %H:%M')})"
