# gestion/services/mascota_service.py

from django.db import transaction

from ..models import Mascota, Dueño, HistoriaClinica


class MascotaService:
    """
    Servicio encargado de la gestión de mascotas,
    dueños y preconsultas.
    """
    @staticmethod
    def buscar_mascota(nombre=None):

        if not nombre:
            return Mascota.objects.none()

        return (
            Mascota.objects
            .select_related("dueño")
            .filter(nombre__icontains=nombre)
            .order_by("nombre")
        )

    @staticmethod
    @transaction.atomic
    def crear_dueño(form):

        return form.save()

    @staticmethod
    @transaction.atomic
    def crear_mascota(form):

        mascota = form.save()

        return mascota
    
    @staticmethod
    @transaction.atomic
    def crear_preconsulta(form, mascota_id):

        if mascota_id:
            form.instance.mascota_id = mascota_id

        consulta = form.save()

        return consulta