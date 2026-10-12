from django.views.generic import ListView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone

from .models import Factura, DetalleFactura
from productos.models import Producto
from gestion_veterinaria.models import HistoriaClinica
from .services.factura_service import FacturaService
from .services.caja_service import CajaService
from gestion_veterinaria.mixins.admin_required import AdminRequiredMixin

# =====================================================================
# VISTAS DEL MÉDICO (Pre-facturación al cerrar la atención)
# =====================================================================

class CargarConceptosConsultaView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'pagos/cargar_conceptos.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 1) Obtener la consulta
        consulta = FacturaService.obtener_consulta(
            self.kwargs["consulta_id"]
        )

        # 2) Obtener o crear la factura borrador
        factura = FacturaService.obtener_o_crear_borrador(
            consulta
        )

        # 3) Mapeo de productos ya seleccionados con su cantidad guardada
        detalles_guardados = {
            d.producto_id: d.cantidad
            for d in factura.detalles.exclude(producto__categoria="HON")
        }

        honorario = FacturaService.obtener_honorarios()
        context["consulta"] = consulta
        context["factura"] = factura
        context["honorario"] = honorario
        context["precio_honorarios"] = float(honorario.precio_unitario)

        medicamentos = list(FacturaService.productos_facturables())
        for prod in medicamentos:
            prod.seleccionado = prod.id in detalles_guardados
            prod.cantidad_actual = detalles_guardados.get(prod.id, 1)

        context["medicamentos_disponibles"] = medicamentos
        context["productos_seleccionados"] = list(detalles_guardados.keys())

        return context

    def post(self, request, *args, **kwargs):
        consulta_id = self.kwargs["consulta_id"]
        seleccionados = request.POST.getlist("medicamentos_seleccionados")

        # Recopilar las cantidades ingresadas por el médico
        cantidades = {}
        for prod_id in seleccionados:
            cant_str = request.POST.get(f"cantidad_{prod_id}", "1")
            try:
                cant = int(cant_str)
                if cant < 1:
                    cant = 1
            except (ValueError, TypeError):
                cant = 1
            cantidades[int(prod_id)] = cant

        FacturaService.actualizar_borrador(
            consulta_id,
            productos_ids=seleccionados,
            cantidades=cantidades
        )

        if request.POST.get("accion") == "guardar":
            return redirect(
                "cargar_conceptos_consulta",
                consulta_id=consulta_id
            )
        elif request.POST.get("accion") == "volver_consulta":
            return redirect(
                "cerrar_consulta",
                pk=consulta_id
            )

        FacturaService.enviar_a_caja(
            consulta_id
        )

        return redirect("consultas_pendientes")


# =====================================================================
# VISTAS DEL OPERADOR (Módulo de Caja y Cobros)
# =====================================================================

# 1. Lista de Cuentas Pendientes (Para el panel del Operador)
class FacturasPendientesListView(LoginRequiredMixin, ListView):
    model = Factura
    template_name = 'pagos/facturas_pendientes.html'
    context_object_name = 'facturas'

    def get_queryset(self):

        return CajaService.pendientes()


# 2. Procesar el Pago de la Factura (Cierre de Caja)
class ProcesarPagoView(LoginRequiredMixin, UpdateView):
    model = Factura
    fields = ['metodo_pago']
    template_name = 'pagos/procesar_pago.html'
    success_url = reverse_lazy('facturas_pendientes')

    def form_valid(self, form):

        CajaService.registrar_pago(form)
        return redirect(self.success_url)