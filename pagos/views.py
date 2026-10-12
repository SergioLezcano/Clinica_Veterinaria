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

        # 3) Enviar datos al template
        context["consulta"] = consulta

        context["factura"] = factura

        context["medicamentos_disponibles"] = (
            FacturaService.productos_facturables()
        )

        context["productos_seleccionados"] = list(

            factura.detalles.exclude( # type: ignore

                producto__categoria="HON"

            ).values_list(

                "producto_id",

                flat=True

            )

        )

        return context

    def post(self, request, *args, **kwargs):

        consulta_id = self.kwargs["consulta_id"]

        FacturaService.actualizar_borrador(
            consulta_id,
            request.POST.getlist("medicamentos_seleccionados")
        )

        if request.POST.get("accion") == "guardar":

            return redirect(
                "cargar_conceptos_consulta",
                consulta_id=consulta_id
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