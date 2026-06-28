from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, CreateView, UpdateView
from django.urls import reverse_lazy

from gestion_veterinaria.mixins.admin_required import AdminRequiredMixin

from .models import Mascota, Dueño, HistoriaClinica
from .forms import MascotaForm, PreConsultaForm
from django.shortcuts import redirect

from .models import PerfilUsuario
from .forms import RegistroOperadorForm

from .services.reporte_service import ReporteService
from .services.historia_service import HistoriaService
from .services.usuario_service import UsuarioService
from .services.mascota_service import MascotaService
from .services.auth_service import AuthService

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
class ConsultasPendientesListView(LoginRequiredMixin, ListView):
    model = HistoriaClinica
    template_name = 'gestion/consultas_pendientes.html'
    context_object_name = 'pendientes'

    def get_queryset(self):
        return HistoriaService.pendientes()

    
class AtenderConsultaView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = HistoriaClinica
    fields = ['peso', 'temperatura', 'diagnostico', 'tratamiento', 'observaciones']
    template_name = 'gestion/cerrar_consulta.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # AGREGAMOS LOS PLACEHOLDERS E INYECTAMOS ATRIBUTOS HTML
        form.fields['peso'].widget.attrs.update({'placeholder': '(en kg)'})
        form.fields['temperatura'].widget.attrs.update({'placeholder': '(en °C)'})
        form.fields['diagnostico'].widget.attrs.update({
            'placeholder': 'Describa el diagnóstico clínico del paciente...',
            'rows': 3
        })
        form.fields['tratamiento'].widget.attrs.update({
            'placeholder': 'Indique medicamentos, dosis y frecuencia...',
            'rows': 3
        })
        form.fields['observaciones'].widget.attrs.update({
            'placeholder': 'Notas adicionales o recordatorios',
            'rows': 2
        })
        return form

    def form_valid(self, form):
        consulta = HistoriaService.completar_consulta(form)
        return redirect(
            "cargar_conceptos_consulta",
            consulta_id=consulta.id
        )
    
    
# Clase para cancelar la preconsulta
class CancelarConsultaView(LoginRequiredMixin, AdminRequiredMixin, TemplateView,):

    def post(self, request, *args, **kwargs):
        HistoriaService.cancelar_consulta(
            self.kwargs["pk"]
        )
        return redirect("consultas_pendientes")


class HistorialClinicoListView(LoginRequiredMixin, ListView):
    model = HistoriaClinica
    template_name = "gestion/historias_clinicas.html"
    context_object_name = "consultas"

    def get_queryset(self):
        return HistoriaService.historial(
            self.request.GET.get("q")
        )

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
        return super().form_valid(form)


# 3. Baja o Alta Lógica (Desactivar/Activar Cuenta)
class CambiarEstadoOperadorView(LoginRequiredMixin, AdminRequiredMixin, TemplateView,):

    def post(self, request, *args, **kwargs):
        UsuarioService.cambiar_estado(
            self.kwargs["pk"]
        )
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
        return redirect(self.success_url) # type: ignore

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

class MascotaCreateView(LoginRequiredMixin, CreateView):
    model = Mascota
    form_class = MascotaForm
    template_name = 'gestion/formulario_mascota.html'
    success_url = reverse_lazy('menu_operador')

    def form_valid(self, form):
        MascotaService.crear_mascota(form)
        return redirect(self.success_url) # type: ignore

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

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
    