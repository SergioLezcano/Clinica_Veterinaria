from decimal import Decimal

from django.db import transaction
from django.db.models import Sum, F, Q, DecimalField
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404

from ..models import Producto
from pagos.models import DetalleFactura


class ProductoService:
    """
    Servicio de lógica de negocio para la gestión de productos, inventario,
    stock y estadísticas de ventas.
    """

    @staticmethod
    def obtener_catalogo(busqueda=None, categoria=None, estado=None, filtro_stock=None):
        """
        Obtiene el catálogo de productos físicos anotando las unidades vendidas
        y recaudación total histórica por producto.
        """
        qs = Producto.objects.exclude(categoria=Producto.Categoria.HONORARIOS)

        if busqueda:
            qs = qs.filter(nombre__icontains=busqueda.strip())

        if categoria and categoria in Producto.Categoria.values:
            qs = qs.filter(categoria=categoria)

        if estado == "activo":
            qs = qs.filter(activo=True)
        elif estado == "inactivo":
            qs = qs.filter(activo=False)

        if filtro_stock == "alerta":
            qs = qs.filter(cantidad__lte=Producto.UMBRAL_STOCK_BAJO)
        elif filtro_stock == "bajo":
            qs = qs.filter(cantidad__gt=0, cantidad__lte=Producto.UMBRAL_STOCK_BAJO)
        elif filtro_stock == "agotado":
            qs = qs.filter(cantidad=0)
        elif filtro_stock == "disponible":
            qs = qs.filter(cantidad__gt=Producto.UMBRAL_STOCK_BAJO)

        # Anotamos ventas históricas confirmadas (facturas pagadas)
        qs = qs.annotate(
            unidades_vendidas=Coalesce(
                Sum(
                    "detalles_factura__cantidad",
                    filter=Q(detalles_factura__factura__estado="PA")
                ),
                0
            ),
            recaudacion_total=Coalesce(
                Sum(
                    "detalles_factura__subtotal",
                    filter=Q(detalles_factura__factura__estado="PA")
                ),
                Decimal("0.00")
            )
        )

        return qs.order_by("nombre")

    @staticmethod
    def obtener_resumen_inventario():
        """
        Calcula indicadores clave del inventario para el dashboard:
        total de ítems, productos con stock bajo (<= 5), agotados y valor total en stock.
        """
        qs = Producto.objects.exclude(categoria=Producto.Categoria.HONORARIOS)

        total_items = qs.count()
        activos = qs.filter(activo=True).count()
        stock_bajo = qs.filter(activo=True, cantidad__gt=0, cantidad__lte=Producto.UMBRAL_STOCK_BAJO).count()
        agotados = qs.filter(activo=True, cantidad=0).count()

        valor_inventario = qs.filter(activo=True).aggregate(
            total=Coalesce(
                Sum(F("precio_unitario") * F("cantidad"), output_field=DecimalField()),
                Decimal("0.00")
            )
        )["total"]

        total_vendido = DetalleFactura.objects.filter(
            factura__estado="PA"
        ).exclude(
            producto__categoria=Producto.Categoria.HONORARIOS
        ).aggregate(
            unidades=Coalesce(Sum("cantidad"), 0),
            monto=Coalesce(Sum("subtotal"), Decimal("0.00"))
        )

        return {
            "total_items": total_items,
            "activos": activos,
            "stock_bajo": stock_bajo,
            "agotados": agotados,
            "total_alertas": stock_bajo + agotados,
            "valor_inventario": valor_inventario,
            "total_unidades_vendidas": total_vendido["unidades"],
            "total_recaudacion_ventas": total_vendido["monto"],
        }

    @staticmethod
    @transaction.atomic
    def ajustar_stock(producto_id, cantidad_delta, modo="agregar"):
        """
        Ajusta la cantidad de stock disponible de un producto.
        - modo='agregar': Suma unidades (ej. recepción de proveedor).
        - modo='establecer': Asigna directamente el inventario físico contado.
        """
        producto = get_object_or_404(Producto, pk=producto_id)

        if modo == "establecer":
            producto.cantidad = max(0, int(cantidad_delta))
        else:
            producto.cantidad = max(0, producto.cantidad + int(cantidad_delta))

        producto.save(update_fields=["cantidad"])
        return producto

    @staticmethod
    @transaction.atomic
    def cambiar_estado(producto_id):
        """
        Pausa o reactiva un producto sin eliminarlo del historial de facturas.
        """
        producto = get_object_or_404(Producto, pk=producto_id)
        producto.activo = not producto.activo
        producto.save(update_fields=["activo"])
        return producto
