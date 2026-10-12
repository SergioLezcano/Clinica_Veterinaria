from django.db import models

class Producto(models.Model):
    class Categoria(models.TextChoices):
        MEDICAMENTO = 'MED', 'Medicamento'
        VACUNA = 'VAC', 'Vacuna'
        INSUMO = 'INS', 'Insumo Clínico'
        HONORARIOS = 'HON', 'Honorarios / Servicios'

    CATEGORIAS = Categoria.choices

    nombre = models.CharField(max_length=100, unique=True)
    categoria = models.CharField(max_length=3, choices=Categoria.choices, default=Categoria.MEDICAMENTO)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True, help_text="Permite desactivar un producto sin borrar su historial")

    UMBRAL_STOCK_BAJO = 5

    @property
    def esta_agotado(self):
        return self.categoria != self.Categoria.HONORARIOS and self.cantidad == 0

    @property
    def stock_bajo(self):
        return self.categoria != self.Categoria.HONORARIOS and 0 < self.cantidad <= self.UMBRAL_STOCK_BAJO

    @property
    def estado_stock(self):
        if self.categoria == self.Categoria.HONORARIOS:
            return "SERVICIO"
        if self.cantidad == 0:
            return "AGOTADO"
        if self.cantidad <= self.UMBRAL_STOCK_BAJO:
            return "BAJO"
        return "DISPONIBLE"

    def __str__(self):
        return f"{self.nombre} (${self.precio_unitario})"

    class Meta:
        verbose_name = "Producto / Servicio"
        verbose_name_plural = "Productos y Servicios"