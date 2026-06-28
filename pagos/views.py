from django.views.generic import ListView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone

from .models import Factura, DetalleFactura
from productos.models import Producto # 👈 IMPORTANTE: Traemos el producto desde su nueva app
from gestion_veterinaria.models import HistoriaClinica

# =====================================================================
# VISTAS DEL MÉDICO (Pre-facturación al cerrar la atención)
# =====================================================================

class CargarConceptosConsultaView(LoginRequiredMixin, TemplateView):
    template_name = 'pagos/cargar_conceptos.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['consulta'] = get_object_or_404(HistoriaClinica, pk=self.kwargs['consulta_id'])
        # Listamos solo los productos/vacunas/medicamentos activos (excluyendo honorarios puros)
        context['medicamentos_disponibles'] = Producto.objects.filter(activo=True).exclude(categoria='HON').order_by('nombre')
        return context

    def post(self, request, *args, **kwargs):
        consulta = get_object_or_404(HistoriaClinica, pk=self.kwargs['consulta_id'])
        
        # Cerramos la consulta clínica
        consulta.estado = 'C'
        consulta.save()

        # Generamos la cabecera de la factura
        factura, creada = Factura.objects.get_or_create(
            consulta=consulta,
            defaults={'estado': 'PE', 'monto_total': 0.00}
        )

        if creada:
            # Buscamos el objeto de Honorarios cargado en el Admin
            honorario_prod = get_object_or_404(
                Producto, 
                nombre="Honorarios por Consulta Médica Veterinaria"
            )
            # Creamos el renglón obligatorio
            DetalleFactura.objects.create(
                factura=factura,
                producto=honorario_prod,
                cantidad=1
            )

        productos_ids = request.POST.getlist('medicamentos_seleccionados')

        # Procesamos si el médico agregó algún medicamento/vacuna extra
        for prod_id in productos_ids:
            if prod_id:
                producto_aplicado = get_object_or_404(Producto, pk=prod_id)
                
                # Evitamos duplicar el producto si por algún motivo ya se había cargado
                if not DetalleFactura.objects.filter(factura=factura, producto=producto_aplicado).exists():
                    DetalleFactura.objects.create(
                        factura=factura,
                        producto=producto_aplicado,
                        cantidad=1 # Por ahora asumimos 1 de cada uno
                    )

        return redirect('consultas_pendientes')


# =====================================================================
# VISTAS DEL OPERADOR (Módulo de Caja y Cobros)
# =====================================================================

# 1. Lista de Cuentas Pendientes (Para el panel del Operador)
class FacturasPendientesListView(LoginRequiredMixin, ListView):
    model = Factura
    template_name = 'pagos/facturas_pendientes.html'
    context_object_name = 'facturas'

    def get_queryset(self):
        # Traemos solo las que faltan pagar, ordenadas de la más nueva a la más vieja
        return Factura.objects.filter(estado='PE').order_by('-fecha_emision')


# 2. Procesar el Pago de la Factura (Cierre de Caja)
class ProcesarPagoView(LoginRequiredMixin, UpdateView):
    model = Factura
    fields = ['metodo_pago']
    template_name = 'pagos/procesar_pago.html'
    success_url = reverse_lazy('facturas_pendientes')

    def form_valid(self, form):
        factura = form.save(commit=False)
        factura.estado = 'PA' # Pasamos el estado a PAGADO
        factura.fecha_pago = timezone.now()
        factura.save()
        return super().form_valid(form)