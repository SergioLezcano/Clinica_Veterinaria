from django.db import transaction
from django.utils import timezone

from ..models import Factura


class CajaService:

    @staticmethod
    def pendientes():

        return (
            Factura.objects
            .filter(
                estado="PE"
            )
            .select_related(
                "consulta",
                "consulta__mascota",
                "consulta__mascota__dueño"
            )
            .order_by("-fecha_emision")
        )
    
    @staticmethod
    @transaction.atomic
    def registrar_pago(form):

        factura = form.save(commit=False)

        factura.estado = "PA"

        factura.fecha_pago = timezone.now()

        factura.save(
            update_fields=[
                "metodo_pago",
                "estado",
                "fecha_pago"
            ]
        )

        return factura