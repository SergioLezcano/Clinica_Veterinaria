# gestion_veterinaria/services/historia_service.py

from django.db.models import Q
from django.db import transaction
from ..models import HistoriaClinica
from django.shortcuts import get_object_or_404


class HistoriaService:

    @staticmethod
    def obtener_por_id(consulta_id):

        return get_object_or_404(
            HistoriaClinica,
            pk=consulta_id
        )

    """ Metodo generico para cambiar de estado """

    @staticmethod
    @transaction.atomic
    def cambiar_estado(consulta_id, estado):
        consulta = HistoriaService.obtener_por_id(consulta_id)
        consulta.estado = estado
        consulta.save(update_fields=["estado"])
        return consulta

    """
    Servicio encargado de toda la lógica relacionada
    con HistoriaClinica.
    """

    @staticmethod
    def pendientes():
        """
        Devuelve las consultas pendientes ordenadas
        por fecha de llegada.
        """

        return (
            HistoriaClinica.objects
            .filter(estado="P")
            .select_related(
                "mascota",
                "mascota__dueño"
            )
            .order_by("fecha_consulta")
        )

    @staticmethod
    def historial(busqueda=None):
        """
        Devuelve el historial clínico.
        Si recibe un texto, filtra por mascota
        o apellido del dueño.
        """

        queryset = (
            HistoriaClinica.objects
            .select_related(
                "mascota",
                "mascota__dueño"
            )
        )

        if busqueda:

            queryset = queryset.filter(
                Q(mascota__nombre__icontains=busqueda)
                |
                Q(mascota__dueño__apellido__icontains=busqueda)
            )

        return queryset.order_by("-fecha_consulta")[:10]
    
    @staticmethod
    def completar_consulta(form):
        consulta = form.save(commit=False)
        consulta.estado = "C"
        consulta.save()
        return consulta
    

    @staticmethod
    @transaction.atomic
    def cancelar_consulta(consulta_id):

        return HistoriaService.cambiar_estado(consulta_id, "X")