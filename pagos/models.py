from decimal import Decimal

from django.db import models
from django.db.models import Sum
from gestion_veterinaria.models import HistoriaClinica
from productos.models import Producto

class Factura(models.Model):
    ESTADOS_PAGO = [
        ('PE', 'Pendiente de Pago'),
        ('PA', 'Pagado'),
        ('CA', 'Cancelado'),
    ]
    
    consulta = models.OneToOneField(HistoriaClinica, on_delete=models.CASCADE, related_name='factura')
    fecha_emision = models.DateTimeField(auto_now_add=True)
    fecha_pago = models.DateTimeField(null=True, blank=True)
    metodo_pago = models.CharField(max_length=2, choices=[('EF', 'Efectivo'), ('TD', 'Tarjeta de Débito'), ('TC', 'Tarjeta de Crédito'), ('TF', 'Transferencia')], null=True, blank=True)
    estado = models.CharField(max_length=2, choices=ESTADOS_PAGO, default='PE')
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00')) #Guarda la suma total

    def actualizar_total(self):
        """
        Calcula la sumatoria de todos los subtotales de sus renglones asociados
        y actualiza el monto_total de la cabecera.
        """
        # Sumamos el campo 'subtotal' de todos los DetalleFactura que apunten a esta factura
        total_detalles = self.detalles.aggregate(total=Sum('subtotal'))['total'] or '0.00'  # type: ignore
        
        # Guardamos el total calculado impactando directamente en la base de datos
        self.monto_total = total_detalles
        self.save(update_fields=['monto_total'])

    def __str__(self):
        return f"Factura #{self.pk} - Consulta #{self.consulta.pk} ({self.get_estado_display()})" # type: ignore


class DetalleFactura(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='detalles_factura')
    cantidad = models.PositiveIntegerField(default=1)
    
    # Clonamos el precio para que si el producto cambia de precio mañana, la factura vieja no se altere
    precio_historico = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        # 1. Traemos el precio unitario del producto desde la app productos y lo congelamos
        if not self.precio_historico:
            self.precio_historico = self.producto.precio_unitario
        
        # 2. Calculamos el subtotal de este renglón (Precio x Cantidad)
        self.subtotal = self.precio_historico * self.cantidad
        
        # 3. Guardamos el renglón de detalle
        super().save(*args, **kwargs)
        
        # 4. 🚀 LA MAGIA: Le ordenamos a la factura padre que recalcule su monto_total
        self.factura.actualizar_total()

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad} (Factura #{self.factura.pk})"