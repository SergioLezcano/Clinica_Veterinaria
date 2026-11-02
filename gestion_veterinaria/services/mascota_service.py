from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from ..models import Mascota, Dueño


class MascotaService:
    """
    Servicio encargado de la gestión de mascotas,
    dueños y preconsultas.
    """
    @staticmethod
    def listar_dueños(termino=None):
        queryset = Dueño.objects.prefetch_related("mascota_set").order_by("apellido", "nombre")

        if termino:
            queryset = queryset.filter(
                Q(nombre__icontains=termino)
                | Q(apellido__icontains=termino)
                | Q(email__icontains=termino)
                | Q(telefono__icontains=termino)
            )

        return queryset

    @staticmethod
    def buscar_mascota(termino=None):

        if not termino:
            return Mascota.objects.none()

        return (
            Mascota.objects
            .select_related("dueño")
            .filter(
                Q(nombre__icontains=termino)
                | Q(dueño__apellido__icontains=termino)
                | Q(dueño__nombre__icontains=termino)
            )
            .order_by("nombre")
        )

    @staticmethod
    @transaction.atomic
    def crear_dueño(form):

        return form.save()

    @staticmethod
    @transaction.atomic
    def actualizar_dueño(form):

        return form.save()

    @staticmethod
    @transaction.atomic
    def crear_mascota(form):

        mascota = form.save()

        return mascota
    
    @staticmethod
    @transaction.atomic
    def crear_preconsulta(form, mascota_id=None):

        if mascota_id:
            mascota = get_object_or_404(Mascota, pk=mascota_id)
            form.instance.mascota = mascota

        consulta = form.save()

        return consulta
