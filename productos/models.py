from django.db import models

class Producto(models.Model):
    CATEGORIAS = [
        ('MED', 'Medicamento'),
        ('VAC', 'Vacuna'),
        ('INS', 'Insumo Clínico'),
        ('HON', 'Honorarios / Servicios'),
    ]

    nombre = models.CharField(max_length=100, unique=True)
    categoria = models.CharField(max_length=3, choices=CATEGORIAS, default='MED')
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True, help_text="Permite desactivar un producto sin borrar su historial")

    def __str__(self):
        return f"{self.nombre} (${self.precio_unitario})"

    class Meta:
        verbose_name = "Producto / Servicio"
        verbose_name_plural = "Productos y Servicios"