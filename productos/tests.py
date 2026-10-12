from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from gestion_veterinaria.models import PerfilUsuario, Dueño, Mascota, HistoriaClinica
from pagos.models import Factura, DetalleFactura
from pagos.services.caja_service import CajaService
from .models import Producto
from .services.producto_service import ProductoService
from .forms import ProductoForm


class CatalogoProductosTests(TestCase):

    def setUp(self):
        # Crear usuario administrador
        self.admin = User.objects.create_superuser(
            username='admin_farmacia',
            email='admin@veterinaria.com',
            password='testpassword123'
        )
        PerfilUsuario.objects.create(
            user=self.admin,
            rol=PerfilUsuario.Rol.ADMINISTRADOR
        )

        # Crear dueño, mascota y consulta para pruebas de facturación
        self.dueño = Dueño.objects.create(
            nombre='Carlos',
            apellido='Gomez',
            telefono='1122334455',
            email='carlos@example.com'
        )
        self.mascota = Mascota.objects.create(
            dueño=self.dueño,
            nombre='Milo',
            especie='Perro',
            raza='Beagle',
            sexo='M'
        )
        self.consulta = HistoriaClinica.objects.create(
            mascota=self.mascota,
            motivo='Vacunación anual y control',
            estado='C'
        )

    def test_creacion_producto_y_umbral_stock_bajo(self):
        """Verifica el alta de productos y que el umbral de 5 unidades active la alerta de stock bajo."""
        # 1. Producto con stock normal (> 5)
        prod_ok = Producto.objects.create(
            nombre='Amoxicilina 500mg',
            categoria=Producto.Categoria.MEDICAMENTO,
            precio_unitario=Decimal('3500.00'),
            cantidad=12
        )
        self.assertFalse(prod_ok.stock_bajo)
        self.assertFalse(prod_ok.esta_agotado)
        self.assertEqual(prod_ok.estado_stock, 'DISPONIBLE')

        # 2. Producto con stock bajo (<= 5)
        prod_bajo = Producto.objects.create(
            nombre='Vacuna Antirrábica',
            categoria=Producto.Categoria.VACUNA,
            precio_unitario=Decimal('5000.00'),
            cantidad=4
        )
        self.assertTrue(prod_bajo.stock_bajo)
        self.assertFalse(prod_bajo.esta_agotado)
        self.assertEqual(prod_bajo.estado_stock, 'BAJO')

        # 3. Producto agotado (0 unidades)
        prod_agotado = Producto.objects.create(
            nombre='Pipeta Antipulgas',
            categoria=Producto.Categoria.MEDICAMENTO,
            precio_unitario=Decimal('2800.00'),
            cantidad=0
        )
        self.assertFalse(prod_agotado.stock_bajo)
        self.assertTrue(prod_agotado.esta_agotado)
        self.assertEqual(prod_agotado.estado_stock, 'AGOTADO')

    def test_validacion_formulario_precio_positivo(self):
        """Verifica que el formulario rechace precios menores o iguales a cero."""
        form_invalido = ProductoForm(data={
            'nombre': 'Jeringa 5ml',
            'categoria': Producto.Categoria.INSUMO,
            'precio_unitario': '0.00',
            'cantidad': '10',
            'activo': True
        })
        self.assertFalse(form_invalido.is_valid())
        self.assertIn('precio_unitario', form_invalido.errors)

    def test_ajustar_stock_reposicion_y_establecer(self):
        """Verifica la reposición por suma y el ajuste por conteo físico directo."""
        producto = Producto.objects.create(
            nombre='Cefalexina 250mg',
            categoria=Producto.Categoria.MEDICAMENTO,
            precio_unitario=Decimal('4200.00'),
            cantidad=3  # Inicialmente en stock bajo
        )
        self.assertTrue(producto.stock_bajo)

        # Reponer 15 unidades (+15)
        ProductoService.ajustar_stock(producto.id, cantidad_delta=15, modo='agregar')
        producto.refresh_from_db()
        self.assertEqual(producto.cantidad, 18)
        self.assertFalse(producto.stock_bajo)

        # Fijar conteo físico exacto a 25
        ProductoService.ajustar_stock(producto.id, cantidad_delta=25, modo='establecer')
        producto.refresh_from_db()
        self.assertEqual(producto.cantidad, 25)

    def test_descuento_stock_al_cobrar_en_caja(self):
        """Verifica que al procesar el pago de la factura en caja se descuente el stock del producto."""
        producto = Producto.objects.create(
            nombre='Vacuna Quíntuple Felina',
            categoria=Producto.Categoria.VACUNA,
            precio_unitario=Decimal('6000.00'),
            cantidad=10  # Stock inicial: 10
        )

        # Crear factura con 3 unidades del producto
        factura = Factura.objects.create(
            consulta=self.consulta,
            estado=Factura.Estado.PENDIENTE,
            monto_total=Decimal('18000.00')
        )
        DetalleFactura.objects.create(
            factura=factura,
            producto=producto,
            cantidad=3
        )

        # Simular que el operador cobra la factura
        class MockForm:
            def save(self, commit=True):
                factura.metodo_pago = Factura.MetodoPago.EFECTIVO
                return factura

        CajaService.registrar_pago(MockForm())

        # Verificar que el stock disminuyó exactamente a 7 unidades
        producto.refresh_from_db()
        self.assertEqual(producto.cantidad, 7)

    def test_cambiar_estado_activa_y_pausa_producto(self):
        """Verifica que el servicio permita pausar y reactivar un producto."""
        producto = Producto.objects.create(
            nombre='Gasas Estériles',
            categoria=Producto.Categoria.INSUMO,
            precio_unitario=Decimal('800.00'),
            cantidad=20,
            activo=True
        )

        # Pausar
        ProductoService.cambiar_estado(producto.id)
        producto.refresh_from_db()
        self.assertFalse(producto.activo)

        # Reactivar
        ProductoService.cambiar_estado(producto.id)
        producto.refresh_from_db()
        self.assertTrue(producto.activo)

    def test_vista_catalogo_muestra_metricas_y_productos(self):
        """Verifica que la vista del catálogo renderice correctamente y muestre los indicadores."""
        self.client.login(username='admin_farmacia', password='testpassword123')

        Producto.objects.create(
            nombre='Ibuprofeno Veterinario',
            categoria=Producto.Categoria.MEDICAMENTO,
            precio_unitario=Decimal('2500.00'),
            cantidad=2  # Stock bajo
        )

        url = reverse('catalogo_productos')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'productos/catalogo.html')
        self.assertContains(response, 'Ibuprofeno Veterinario')
        self.assertContains(response, 'Farmacia y Catálogo de Productos')
        self.assertEqual(response.context['resumen']['stock_bajo'], 1)
