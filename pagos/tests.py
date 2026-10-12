from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from gestion_veterinaria.models import Dueño, Mascota, HistoriaClinica, PerfilUsuario
from productos.models import Producto
from pagos.models import Factura, DetalleFactura
from pagos.services.factura_service import FacturaService
from pagos.services.caja_service import CajaService


class FacturaServiceTests(TestCase):
    def setUp(self):
        self.medico = User.objects.create_superuser(
            username='veterinario',
            password='testpassword123'
        )
        PerfilUsuario.objects.create(
            user=self.medico,
            rol=PerfilUsuario.Rol.ADMINISTRADOR
        )
        self.dueño = Dueño.objects.create(
            nombre='Ana',
            apellido='Martinez',
            telefono='3794123456',
            email='ana@example.com'
        )
        self.mascota = Mascota.objects.create(
            dueño=self.dueño,
            nombre='Rocky',
            especie='Canino',
            raza='Boxer',
            sexo=Mascota.Sexo.MACHO
        )
        self.consulta = HistoriaClinica.objects.create(
            mascota=self.mascota,
            motivo='Control y vacunación',
            diagnostico='Paciente saludable',
            estado='C'
        )
        self.vacuna = Producto.objects.create(
            nombre='Vacuna Antirrábica',
            categoria=Producto.Categoria.VACUNA,
            precio_unitario=Decimal("4000.00"),
            activo=True
        )
        self.antiparasitario = Producto.objects.create(
            nombre='Antiparasitario Comprimido',
            categoria=Producto.Categoria.MEDICAMENTO,
            precio_unitario=Decimal("2500.00"),
            activo=True
        )

    def test_crear_borrador_incluye_honorarios(self):
        """Verifica que el borrador incluya honorarios automáticamente por defecto."""
        factura = FacturaService.obtener_o_crear_borrador(self.consulta)
        self.assertEqual(factura.estado, Factura.Estado.BORRADOR)
        self.assertEqual(factura.detalles.count(), 1)
        detalle_honorario = factura.detalles.first()
        self.assertEqual(detalle_honorario.producto.categoria, 'HON')
        self.assertEqual(factura.monto_total, Decimal("10000.00"))

    def test_actualizar_borrador_con_multiples_cantidades(self):
        """Verifica que al seleccionar múltiples cantidades de productos se multiplique el subtotal y el total."""
        factura = FacturaService.obtener_o_crear_borrador(self.consulta)

        productos_ids = [self.vacuna.id, self.antiparasitario.id]
        cantidades = {
            self.vacuna.id: 2,           # 2 * 4000 = 8000
            self.antiparasitario.id: 3,  # 3 * 2500 = 7500
        }

        factura_actualizada = FacturaService.actualizar_borrador(
            consulta_id=self.consulta.id,
            productos_ids=productos_ids,
            cantidades=cantidades
        )

        detalles = factura_actualizada.detalles.all()
        # 1 honorario + 2 productos = 3 detalles
        self.assertEqual(detalles.count(), 3)

        det_vacuna = detalles.get(producto=self.vacuna)
        self.assertEqual(det_vacuna.cantidad, 2)
        self.assertEqual(det_vacuna.subtotal, Decimal("8000.00"))

        det_anti = detalles.get(producto=self.antiparasitario)
        self.assertEqual(det_anti.cantidad, 3)
        self.assertEqual(det_anti.subtotal, Decimal("7500.00"))

        # Total esperado: 10000 (honorarios) + 8000 + 7500 = 25500
        self.assertEqual(factura_actualizada.monto_total, Decimal("25500.00"))

    def test_post_cargar_conceptos_vista(self):
        """Verifica que la vista procese correctamente los campos cantidad_{id}."""
        self.client.login(username='veterinario', password='testpassword123')

        url = reverse('cargar_conceptos_consulta', kwargs={'consulta_id': self.consulta.id})
        post_data = {
            'medicamentos_seleccionados': [str(self.vacuna.id), str(self.antiparasitario.id)],
            f'cantidad_{self.vacuna.id}': '3',          # 3 * 4000 = 12000
            f'cantidad_{self.antiparasitario.id}': '2', # 2 * 2500 = 5000
            'accion': 'enviar'
        }

        response = self.client.post(url, data=post_data)
        # Redirige a consultas_pendientes al enviar a caja
        self.assertRedirects(response, reverse('consultas_pendientes'))

        factura = Factura.objects.get(consulta=self.consulta)
        self.assertEqual(factura.estado, Factura.Estado.PENDIENTE)
        # Total esperado: 10000 + 12000 + 5000 = 27000.00
        self.assertEqual(factura.monto_total, Decimal("27000.00"))

        det_vacuna = factura.detalles.get(producto=self.vacuna)
        self.assertEqual(det_vacuna.cantidad, 3)
        self.assertEqual(det_vacuna.subtotal, Decimal("12000.00"))

    def test_get_cargar_conceptos_template_renders(self):
        """Verifica que el template renderice sin errores de sintaxis en GET."""
        self.client.login(username='veterinario', password='testpassword123')
        url = reverse('cargar_conceptos_consulta', kwargs={'consulta_id': self.consulta.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pagos/cargar_conceptos.html')
        self.assertContains(response, 'Pre-facturación de Atención')
        self.assertContains(response, self.vacuna.nombre)
        self.assertContains(response, self.antiparasitario.nombre)
        self.assertContains(response, 'Volver a la Consulta')

    def test_post_cargar_conceptos_volver_a_consulta(self):
        """Verifica que 'Volver a la Consulta' guarde el borrador y redirija a cerrar_consulta."""
        self.client.login(username='veterinario', password='testpassword123')

        url = reverse('cargar_conceptos_consulta', kwargs={'consulta_id': self.consulta.id})
        post_data = {
            'medicamentos_seleccionados': [str(self.vacuna.id)],
            f'cantidad_{self.vacuna.id}': '2',
            'accion': 'volver_consulta'
        }

        response = self.client.post(url, data=post_data)
        # Debe redirigir a cerrar_consulta (pk=self.consulta.id)
        self.assertRedirects(response, reverse('cerrar_consulta', kwargs={'pk': self.consulta.id}))

        # La factura debe mantenerse en estado BORRADOR y con los productos guardados
        factura = Factura.objects.get(consulta=self.consulta)
        self.assertEqual(factura.estado, Factura.Estado.BORRADOR)
        det_vacuna = factura.detalles.get(producto=self.vacuna)
        self.assertEqual(det_vacuna.cantidad, 2)

    def test_flujo_edicion_consulta_y_retorno_a_prefactura(self):
        """Verifica que al volver a cerrar_consulta se pueda editar el diagnóstico y continuar sin perder la factura."""
        self.client.login(username='veterinario', password='testpassword123')

        # 1. Crear borrador inicial con producto
        FacturaService.obtener_o_crear_borrador(self.consulta)
        FacturaService.actualizar_borrador(
            self.consulta.id,
            productos_ids=[self.vacuna.id],
            cantidades={self.vacuna.id: 2}
        )

        # 2. Visitar cerrar_consulta
        url_consulta = reverse('cerrar_consulta', kwargs={'pk': self.consulta.id})
        get_response = self.client.get(url_consulta)
        self.assertEqual(get_response.status_code, 200)
        self.assertTrue(get_response.context['tiene_borrador'])
        self.assertContains(get_response, 'Pre-factura en curso')

        # 3. Guardar diagnóstico actualizado en cerrar_consulta
        post_data = {
            'peso': '12.5',
            'temperatura': '38.5',
            'diagnostico': 'Diagnóstico actualizado con precisión',
            'tratamiento': 'Continuar con vacuna programada',
            'observaciones': 'Sin complicaciones',
        }
        post_response = self.client.post(url_consulta, data=post_data)

        # Debe redirigir de nuevo a cargar_conceptos_consulta
        self.assertRedirects(
            post_response,
            reverse('cargar_conceptos_consulta', kwargs={'consulta_id': self.consulta.id})
        )

        # Verificar que el diagnóstico se actualizó
        self.consulta.refresh_from_db()
        self.assertEqual(self.consulta.diagnostico, 'Diagnóstico actualizado con precisión')

        # Verificar que la factura borrador no se perdió y mantiene sus detalles
        factura = Factura.objects.get(consulta=self.consulta)
        self.assertEqual(factura.estado, Factura.Estado.BORRADOR)
        self.assertTrue(factura.detalles.filter(producto=self.vacuna).exists())
        self.assertEqual(factura.detalles.get(producto=self.vacuna).cantidad, 2)

    def test_consultas_pendientes_muestra_borradores_no_enviados(self):
        """Verifica que la sala de espera muestre la sección de borradores para consultas no enviadas a caja."""
        self.client.login(username='veterinario', password='testpassword123')

        # La consulta actual está completada con borrador
        self.consulta.estado = 'C'
        self.consulta.save()
        FacturaService.obtener_o_crear_borrador(self.consulta)

        url = reverse('consultas_pendientes')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('borradores', response.context)
        self.assertIn(self.consulta, response.context['borradores'])
        self.assertContains(response, 'Pre-facturas en Borrador / En Curso')


