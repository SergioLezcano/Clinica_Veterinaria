from decimal import Decimal

from django.db import models
from django.db.models import Sum

from gestion_veterinaria.models import HistoriaClinica
from productos.models import Producto


class Factura(models.Model):

    class Estado(models.TextChoices):
        BORRADOR = "BO", "Borrador"
        PENDIENTE = "PE", "Pendiente de Pago"
        PAGADO = "PA", "Pagado"
        CANCELADO = "CA", "Cancelado"

    class MetodoPago(models.TextChoices):
        EFECTIVO = "EF", "Efectivo"
        TARJETA_DEBITO = "TD", "Tarjeta de Débito"
        TARJETA_CREDITO = "TC", "Tarjeta de Crédito"
        TRANSFERENCIA = "TF", "Transferencia"

    consulta = models.OneToOneField(
        HistoriaClinica,
        on_delete=models.CASCADE,
        related_name="factura"
    )

    fecha_emision = models.DateTimeField(
        auto_now_add=True
    )

    fecha_pago = models.DateTimeField(
        null=True,
        blank=True
    )

    metodo_pago = models.CharField(
        max_length=2,
        choices=MetodoPago.choices,
        null=True,
        blank=True
    )

    estado = models.CharField(
        max_length=2,
        choices=Estado.choices,
        default=Estado.PENDIENTE
    )

    monto_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    def actualizar_total(self):
        """
        Recalcula el total de la factura a partir
        de sus detalles.
        """

        total = (
            self.detalles.aggregate( # type: ignore
                total=Sum("subtotal")
            )["total"]
            or Decimal("0.00")
        )

        self.monto_total = total

        self.save(
            update_fields=["monto_total"]
        )

    def __str__(self):

        return (
            f"Factura #{self.pk}"
            f" - Consulta #{self.consulta.pk}"
        )


class DetalleFactura(models.Model):

    factura = models.ForeignKey(Factura,on_delete=models.CASCADE,related_name="detalles")
    producto = models.ForeignKey(Producto,on_delete=models.PROTECT,related_name="detalles_factura")
    cantidad = models.PositiveIntegerField(default=1)
    precio_historico = models.DecimalField(max_digits=10,decimal_places=2,editable=False)
    subtotal = models.DecimalField(max_digits=10,decimal_places=2,editable=False)

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=["factura", "producto"],
                name="unique_producto_factura"
            )
        ]
        ordering = ["id"]

    def save(self, *args, **kwargs):

        if self._state.adding:
            self.precio_historico = self.producto.precio_unitario

        self.subtotal = (
            self.precio_historico * self.cantidad
        )

        super().save(*args, **kwargs)

    def __str__(self):

        return (
            f"{self.producto.nombre}"
            f" x {self.cantidad}"
        )