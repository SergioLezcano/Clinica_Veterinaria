from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, CreateView, UpdateView
from django.urls import reverse_lazy

from .models import Mascota, Dueño, HistoriaClinica
from .forms import MascotaForm, PreConsultaForm
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Q

from django.contrib.auth.models import User
from .models import PerfilUsuario
from .forms import RegistroOperadorForm

from django.db.models import Count
from django.utils import timezone

# ==========================================
# 🔄 REDIRECCIÓN E INICIO (POST-LOGIN)
# ==========================================

def redireccionar_segun_rol(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        perfil = request.user.perfilusuario
        # Maneja tanto 'ADMIN' como las variantes de operador
        if perfil.rol == 'ADMIN':
            return redirect('menu_administrador')
        elif perfil.rol in ['OPER', 'OPERADOR', 'OPERER']:
            return redirect('menu_operador')
    except Exception:
        return redirect('login')


# ==========================================
# 🖥️ SECCIÓN DEL ADMINISTRADOR (MÉDICO)
# ==========================================

class MenuAdministradorView(LoginRequiredMixin, TemplateView):
    template_name = 'gestion/menu_administrador.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.perfilusuario.rol != 'ADMIN':
            return redirect('menu_operador')
        return super().dispatch(request, *args, **kwargs)

# El médico visualiza la sala de espera virtual (Consultas con estado 'P' de Pendiente)
class ConsultasPendientesListView(LoginRequiredMixin, ListView):
    model = HistoriaClinica
    template_name = 'gestion/consultas_pendientes.html'
    context_object_name = 'pendientes'

    def get_queryset(self):
        # Filtra las consultas pendientes y las ordena por orden de llegada (antigüedad)
        return HistoriaClinica.objects.filter(estado='P').order_by('fecha_consulta')

    def dispatch(self, request, *args, **kwargs):
        if request.user.perfilusuario.rol != 'ADMIN':
            return redirect('menu_operador')
        return super().dispatch(request, *args, **kwargs)

    
class AtenderConsultaView(LoginRequiredMixin, UpdateView):
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
        # 1. Guardamos de forma limpia los datos del formulario clínico
        consulta = form.save(commit=False)
        consulta.estado = 'C' # Pasamos el estado de Pendiente ('P') a Completada ('C')
        consulta.save()

        # 2. 🚀 REDIRECCIÓN CLAVE: Mandamos al médico directo a cargar los productos/honorarios
        # Usamos 'consulta_id' para que encaje directo con la URL de pre-facturación que armamos
        return redirect('cargar_conceptos_consulta', consulta_id=consulta.id)

    def dispatch(self, request, *args, **kwargs):
        # Candado de seguridad: si no es médico (ADMIN), lo saca volando al menú operador
        if request.user.perfilusuario.rol != 'ADMIN':
            return redirect('menu_operador')
        return super().dispatch(request, *args, **kwargs)
    
# función para cancelar la preconsulta
class CancelarConsultaView(LoginRequiredMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        # Buscamos la consulta por su ID (pk)
        consulta = get_object_or_404(HistoriaClinica, pk=self.kwargs['pk'])
        
        # Doble candado de seguridad por rol
        if request.user.perfilusuario.rol == 'ADMIN':
            consulta.estado = 'X' # Marcamos como cancelada
            consulta.save()
            
        return redirect('consultas_pendientes')


class HistorialClinicoListView(LoginRequiredMixin, ListView):
    model = HistoriaClinica
    template_name = 'gestion/historias_clinicas.html'
    context_object_name = 'consultas'

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            # ⚡ BUSCADOR AVANZADO: Busca por nombre de mascota O por apellido del dueño
            return HistoriaClinica.objects.filter(
                Q(mascota__nombre__icontains=query) | 
                Q(mascota__dueño__apellido__icontains=query)
            ).order_by('-fecha_consulta') # El signo menos (-) hace que muestre primero lo último que pasó
        
        # Si no buscó nada, muestra las últimas 10 consultas generales del hospital como historial reciente
        return HistoriaClinica.objects.all().order_by('-fecha_consulta')[:10]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['busqueda'] = self.request.GET.get('q', '')
        return context

# SECCION PARA DAR DE ALTA UN NUEVO USUARIO
# 1. Lista de Operadores (Para ver quiénes están activos y quiénes dados de baja)
class OperadoresListView(LoginRequiredMixin, ListView):
    model = PerfilUsuario
    template_name = 'gestion/gestion_operadores.html'
    context_object_name = 'operadores'

    def get_queryset(self):
        # Traemos todos los perfiles cuyo rol sea OPERADOR u OPER
        return PerfilUsuario.objects.filter(rol__in=['OPER', 'OPERADOR', 'OPERER'])

    def dispatch(self, request, *args, **kwargs):
        if request.user.perfilusuario.rol != 'ADMIN':
            return redirect('menu_operador')
        return super().dispatch(request, *args, **kwargs)

# 2. Alta de Operador
class OperadorCreateView(LoginRequiredMixin, CreateView):
    form_class = RegistroOperadorForm
    template_name = 'gestion/alta_operador.html'
    success_url = reverse_lazy('gestion_operadores')

    def form_valid(self, form):
        # Guardamos el usuario base de Django
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        
        # Le creamos su PerfilUsuario automáticamente con rol OPERADOR
        PerfilUsuario.objects.create(user=user, rol='OPER')
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if request.user.perfilusuario.rol != 'ADMIN':
            return redirect('menu_operador')
        return super().dispatch(request, *args, **kwargs)

# 3. Baja o Alta Lógica (Desactivar/Activar Cuenta)
class CambiarEstadoOperadorView(LoginRequiredMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        if request.user.perfilusuario.rol == 'ADMIN':
            # Buscamos al usuario de Django por su ID
            usuario_operador = get_object_or_404(User, pk=self.kwargs['pk'])
            # Invertimos su estado de actividad (si estaba activo pasa a inactivo, y viceversa)
            usuario_operador.is_active = not usuario_operador.is_active
            usuario_operador.save()
            
        return redirect('gestion_operadores')


# ==========================================
#  recep SECCIÓN DEL OPERADOR (RECEPCIÓN)
# ==========================================

class MenuOperadorView(LoginRequiredMixin, ListView):
    model = Mascota
    template_name = 'gestion/menu_operador.html'
    context_object_name = 'mascotas_encontradas'

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return Mascota.objects.filter(nombre__icontains=query)
        return Mascota.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['busqueda'] = self.request.GET.get('q', '')
        return context

class DuenoCreateView(LoginRequiredMixin, CreateView):
    model = Dueño
    fields = ['nombre', 'apellido', 'telefono', 'email'] 
    template_name = 'gestion/formulario_dueño.html'
    success_url = reverse_lazy('menu_operador')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

class MascotaCreateView(LoginRequiredMixin, CreateView):
    model = Mascota
    form_class = MascotaForm
    template_name = 'gestion/formulario_mascota.html'
    success_url = reverse_lazy('menu_operador') 

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
        mascota_id = self.request.GET.get('mascota_id')
        if mascota_id:
            # Forzamos la mascota en la instancia del modelo antes de guardar
            form.instance.mascota_id = mascota_id
        return super().form_valid(form)
    

######## SECCION DE REPORTES ESTADISTICOS #######

class ReportesEstadisticosView(LoginRequiredMixin, TemplateView):
    template_name = 'gestion/reportes_estadisticos.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = timezone.now().date()

        # 1. Totales Generales de la historia del consultorio
        consultas_totales = HistoriaClinica.objects.count()
        context['totales'] = {
            'completadas': HistoriaClinica.objects.filter(estado='C').count(),
            'en_espera': HistoriaClinica.objects.filter(estado='P').count(),
            'canceladas': HistoriaClinica.objects.filter(estado='X').count(),
        }

        # 2. Movimiento de HOY (Métricas operativas diarias)
        consultas_hoy = HistoriaClinica.objects.filter(fecha_consulta__date=hoy)
        context['hoy'] = {
            'atendidos': consultas_hoy.filter(estado='C').count(),
            'espera': consultas_hoy.filter(estado='P').count(),
        }

        # 3. Distribución por Especie (Top 3)
        # Esto agrupa por la columna 'especie' de la mascota y cuenta cuántas hay
        especies_data = HistoriaClinica.objects.filter(estado='C')\
            .values('mascota__especie')\
            .annotate(total=Count('id'))\
            .order_by('-total')[:3]
        
        # Procesamos los porcentajes para las barras de CSS
        total_atendidos = context['totales']['completadas'] or 1 # Evitamos división por cero
        especies_lista = []
        for item in especies_data:
            porcentaje = int((item['total'] / total_atendidos) * 100)
            especies_lista.append({
                'nombre': item['mascota__especie'].capitalize(),
                'cantidad': item['total'],
                'porcentaje': porcentaje
            })
        
        context['especies'] = especies_lista
        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.perfilusuario.rol != 'ADMIN':
            return redirect('menu_operador')
        return super().dispatch(request, *args, **kwargs)