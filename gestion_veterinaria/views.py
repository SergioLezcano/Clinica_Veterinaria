from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import TemplateView, ListView, CreateView, UpdateView
from django.urls import reverse_lazy

from gestion_veterinaria.mixins.admin_required import AdminRequiredMixin

from .models import Mascota, Dueño, HistoriaClinica
from .forms import MascotaForm, PreConsultaForm, CierreConsultaForm
from django.shortcuts import redirect

from .models import PerfilUsuario
from .forms import RegistroOperadorForm

from .services.reporte_service import ReporteService
from .services.historia_service import HistoriaService
from .services.usuario_service import UsuarioService
from .services.mascota_service import MascotaService
from .services.auth_service import AuthService
from pagos.services.factura_service import FacturaService

# ==========================================
# 🔄 REDIRECCIÓN E INICIO (POST-LOGIN)
# ==========================================

def redireccionar_segun_rol(request):
    return AuthService.redireccionar_por_rol(request.user)


# ==========================================
# 🖥️ SECCIÓN DEL ADMINISTRADOR (MÉDICO)
# ==========================================

class MenuAdministradorView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'gestion/menu_administrador.html'



# El médico visualiza la sala de espera virtual (Consultas con estado 'P' de Pendiente)
class ConsultasPendientesListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = HistoriaClinica
    template_name = 'gestion/consultas_pendientes.html'
    context_object_name = 'pendientes'

    def get_queryset(self):
        return HistoriaService.pendientes()

    
class AtenderConsultaView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = HistoriaClinica
    form_class = CierreConsultaForm
    template_name = 'gestion/cerrar_consulta.html'

    def form_valid(self, form):
        consulta = HistoriaService.completar_consulta(form)

        FacturaService.obtener_o_crear_borrador(consulta)

        return redirect(
            "cargar_conceptos_consulta",
            consulta_id=consulta.id
        )
    
    
# Clase para cancelar la preconsulta
class CancelarConsultaView(LoginRequiredMixin, AdminRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        HistoriaService.cancelar_consulta(
            self.kwargs["pk"]
        )
        return redirect("consultas_pendientes")

    def get(self, request, *args, **kwargs):
        return redirect("consultas_pendientes")


class HistorialClinicoListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = HistoriaClinica
    template_name = "gestion/historias_clinicas.html"
    context_object_name = "consultas"

    def get_queryset(self):
        return HistoriaService.historial(
            self.request.GET.get("q")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['busqueda'] = self.request.GET.get('q', '')
        return context

# SECCION PARA DAR DE ALTA UN NUEVO USUARIO
# 1. Lista de Operadores (Para ver quiénes están activos y quiénes dados de baja)
class OperadoresListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = PerfilUsuario
    template_name = 'gestion/gestion_operadores.html'
    context_object_name = 'operadores'

    def get_queryset(self):
        return UsuarioService.obtener_operadores()


# 2. Alta de Operador
class OperadorCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    form_class = RegistroOperadorForm
    template_name = 'gestion/alta_operador.html'
    success_url = reverse_lazy('gestion_operadores')

    def form_valid(self, form):
        UsuarioService.crear_operador(form)
        return redirect(self.success_url)


# 3. Baja o Alta Lógica (Desactivar/Activar Cuenta)
class CambiarEstadoOperadorView(LoginRequiredMixin, AdminRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        UsuarioService.cambiar_estado(
            self.kwargs["pk"]
        )
        return redirect("gestion_operadores")

    def get(self, request, *args, **kwargs):
        return redirect("gestion_operadores")
    
######## SECCION DE REPORTES ESTADISTICOS #######

class ReportesEstadisticosView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):

    template_name = 'gestion/reportes_estadisticos.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['totales'] = (
            ReporteService.obtener_totales()
        )

        context['hoy'] = (
            ReporteService.obtener_movimiento_hoy()
        )

        context["especies"] = ReporteService.top_especies(
            context["totales"]["completadas"]
        )

        return context

# ==========================================
#  SECCIÓN DEL OPERADOR (RECEPCIÓN)
# ==========================================

class MenuOperadorView(LoginRequiredMixin, ListView):
    model = Mascota
    template_name = 'gestion/menu_operador.html'
    context_object_name = 'mascotas_encontradas'

    def get_queryset(self):
        return MascotaService.buscar_mascota(
            self.request.GET.get("q")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['busqueda'] = self.request.GET.get('q', '')
        return context

class DuenoCreateView(LoginRequiredMixin, CreateView):
    model = Dueño
    fields = ['nombre', 'apellido', 'telefono', 'email'] 
    template_name = 'gestion/formulario_dueño.html'
    success_url = reverse_lazy('menu_operador')

    def form_valid(self, form):
        MascotaService.crear_dueño(form)
        return redirect(self.success_url)

class MascotaCreateView(LoginRequiredMixin, CreateView):
    model = Mascota
    form_class = MascotaForm
    template_name = 'gestion/formulario_mascota.html'
    success_url = reverse_lazy('menu_operador')

    def form_valid(self, form):
        MascotaService.crear_mascota(form)
        return redirect(self.success_url)

# El operador inicia la orden corta de consultorio (Solo Mascota y Motivo)
class PreConsultaCreateView(LoginRequiredMixin, CreateView):
    model = HistoriaClinica
    form_class = PreConsultaForm  
    template_name = 'gestion/formulario_preconsulta.html'
    success_url = reverse_lazy('menu_operador')

    def get_initial(self):
        initial = super().get_initial()
        mascota_id = self.request.GET.get('mascota_id')
        if mascota_id:
            initial['mascota'] = mascota_id
        return initial
    
    def form_valid(self, form):
        MascotaService.crear_preconsulta(
            form,
            self.request.GET.get("mascota_id")
        )
        return redirect(self.success_url) # type: ignore
    