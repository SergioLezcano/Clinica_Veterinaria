from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView

from gestion_veterinaria.mixins.admin_required import AdminRequiredMixin
from .models import Producto
from .forms import ProductoForm, AjustarStockForm
from .services.producto_service import ProductoService


class CatalogoProductosView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """
    Catálogo interactivo de productos y medicamentos con control de stock,
    indicadores de inventario y estadísticas de ventas.
    """
    model = Producto
    template_name = "productos/catalogo.html"
    context_object_name = "productos"

    def get_queryset(self):
        busqueda = self.request.GET.get("q", "")
        categoria = self.request.GET.get("categoria", "")
        estado = self.request.GET.get("estado", "")
        filtro_stock = self.request.GET.get("stock", "")

        return ProductoService.obtener_catalogo(
            busqueda=busqueda,
            categoria=categoria,
            estado=estado,
            filtro_stock=filtro_stock
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["resumen"] = ProductoService.obtener_resumen_inventario()
        context["busqueda"] = self.request.GET.get("q", "")
        context["categoria_sel"] = self.request.GET.get("categoria", "")
        context["estado_sel"] = self.request.GET.get("estado", "")
        context["stock_sel"] = self.request.GET.get("stock", "")
        context["categorias"] = [
            (c.value, c.label) for c in Producto.Categoria if c != Producto.Categoria.HONORARIOS
        ]
        context["form_ajuste"] = AjustarStockForm()
        return context

    def post(self, request, *args, **kwargs):
        return redirect("catalogo_productos")


class ProductoCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """
    Alta de nuevo producto o medicamento en el catálogo.
    """
    model = Producto
    form_class = ProductoForm
    template_name = "productos/form_producto.html"
    success_url = reverse_lazy("catalogo_productos")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Producto '{self.object.nombre}' agregado con éxito al catálogo con stock inicial de {self.object.cantidad} unidades."
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Nuevo Producto / Medicamento"
        context["subtitulo"] = "Completá los datos para incorporar el producto al inventario clínico"
        context["accion_btn"] = "Guardar Producto"
        return context


class ProductoUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """
    Edición de datos, precios y categorías de un producto existente.
    """
    model = Producto
    form_class = ProductoForm
    template_name = "productos/form_producto.html"
    success_url = reverse_lazy("catalogo_productos")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Producto '{self.object.nombre}' actualizado correctamente (Precio: ${self.object.precio_unitario})."
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = f"Editar: {self.object.nombre}"
        context["subtitulo"] = "Actualizá el precio, categoría o estado del producto"
        context["accion_btn"] = "Guardar Cambios"
        return context


class AjustarStockView(LoginRequiredMixin, AdminRequiredMixin, View):
    """
    Acción rápida para reponer o ajustar stock desde el catálogo.
    """
    def post(self, request, pk):
        cantidad = request.POST.get("cantidad")
        modo = request.POST.get("modo", "agregar")

        try:
            cantidad_int = int(cantidad)
            if cantidad_int < 0:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, "La cantidad ingresada no es válida.")
            return redirect("catalogo_productos")

        producto = ProductoService.ajustar_stock(
            producto_id=pk,
            cantidad_delta=cantidad_int,
            modo=modo
        )

        accion_txt = "repuso" if modo == "agregar" else "estableció"
        messages.success(
            request,
            f"Stock de '{producto.nombre}' actualizado exitosamente: {producto.cantidad} unidades disponibles."
        )
        return redirect("catalogo_productos")

    def get(self, request, pk):
        return redirect("catalogo_productos")


class CambiarEstadoProductoView(LoginRequiredMixin, AdminRequiredMixin, View):
    """
    Activar o pausar un producto para la venta/aplicación sin borrarlo.
    """
    def post(self, request, pk):
        producto = ProductoService.cambiar_estado(pk)
        estado_txt = "activado" if producto.activo else "pausado para la venta"
        messages.info(
            request,
            f"El producto '{producto.nombre}' ahora se encuentra {estado_txt}."
        )
        return redirect("catalogo_productos")

    def get(self, request, pk):
        return redirect("catalogo_productos")
