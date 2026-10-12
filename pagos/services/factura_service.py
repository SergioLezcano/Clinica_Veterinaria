from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404

from gestion_veterinaria.models import HistoriaClinica
from productos.models import Producto

from ..models import Factura, DetalleFactura


class FacturaService:

    @staticmethod
    def obtener_consulta(consulta_id):

        return get_object_or_404(
            HistoriaClinica.objects.select_related(
                "mascota",
                "mascota__dueño"
            ),
            pk=consulta_id
        )

    @staticmethod
    def productos_facturables():

        return (
            Producto.objects
            .filter(activo=True)
            .exclude(categoria="HON")
            .order_by("nombre")
        )

    @staticmethod
    def obtener_honorarios():

        honorario = Producto.objects.filter(
            categoria="HON",
            activo=True
        ).first()

        if not honorario:
            honorario, _ = Producto.objects.get_or_create(
                nombre="Honorarios por Consulta Médica Veterinaria",
                defaults={
                    "categoria": "HON",
                    "precio_unitario": Decimal("10000.00"),
                    "activo": True,
                }
            )

        return honorario

    @staticmethod
    def agregar_producto(factura, producto, cantidad=1):

        detalle, creado = DetalleFactura.objects.get_or_create(
            factura=factura,
            producto=producto,
            defaults={
                "cantidad": cantidad
            }
        )

        if not creado:
            detalle.cantidad += cantidad
            detalle.save()

        return detalle

    @staticmethod
    @transaction.atomic
    def generar_desde_consulta(
        consulta_id,
        productos_ids
    ):

        consulta = FacturaService.obtener_consulta(
            consulta_id
        )

        factura, creada = Factura.objects.get_or_create(
            consulta=consulta,
            defaults={
                "estado": Factura.Estado.PENDIENTE,
                "monto_total": Decimal("0.00"),
            }
        )

        if creada:
            FacturaService.agregar_producto(
                factura,
                FacturaService.obtener_honorarios()
            )

        productos = Producto.objects.filter(
            pk__in=[pid for pid in productos_ids if pid],
            activo=True
        )

        for producto in productos:
            FacturaService.agregar_producto(
                factura,
                producto
            )
        # Se recalcula una única vez
        factura.actualizar_total()

        return factura
    
    @staticmethod
    @transaction.atomic
    def obtener_o_crear_borrador(consulta):

        factura, creada = Factura.objects.get_or_create(

            consulta=consulta,

            defaults={

                "estado": Factura.Estado.BORRADOR

            }

        )

        if creada:

            FacturaService.agregar_producto(

                factura,

                FacturaService.obtener_honorarios()

            )

            factura.actualizar_total()

        return factura
    
    @staticmethod
    @transaction.atomic
    def actualizar_borrador(
        consulta_id,
        productos_ids,
    ):

        consulta = FacturaService.obtener_consulta(
            consulta_id
        )

        factura = FacturaService.obtener_o_crear_borrador(
            consulta
        )

        # Eliminamos todos los productos excepto Honorarios
        factura.detalles.exclude(
            producto__categoria="HON"
        ).delete()

        # Agregamos nuevamente los seleccionados
        productos = Producto.objects.filter(
            pk__in=productos_ids,
            activo=True
        )

        for producto in productos:

            FacturaService.agregar_producto(
                factura,
                producto
            )

        factura.actualizar_total()

        return factura
    
    @staticmethod
    @transaction.atomic
    def enviar_a_caja(consulta_id):

        consulta = FacturaService.obtener_consulta(
            consulta_id
        )

        factura = consulta.factura # type: ignore

        factura.estado = Factura.Estado.PENDIENTE

        factura.save(
            update_fields=["estado"]
        )

        return factura