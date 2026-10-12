from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, CreateView

from gestion_veterinaria.services.auth_service import AuthService
from .forms import TurnoForm
from .models import Turno
from .services.turno_service import TurnoService


class CalendarioTurnosView(LoginRequiredMixin, TemplateView):
    """
    Vista principal de la agenda con calendario interactivo para operadores y médicos.
    """
    template_name = 'turnos/calendario.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        es_admin = AuthService.es_admin(self.request.user)
        context['es_admin'] = es_admin
        context['url_volver'] = 'menu_administrador' if es_admin else 'menu_operador'
        context['form'] = TurnoForm()
        context['total_pendientes'] = Turno.objects.filter(estado=Turno.Estado.PENDIENTE).count()
        context['total_confirmados'] = Turno.objects.filter(estado=Turno.Estado.CONFIRMADO).count()
        context['ultimos_turnos'] = TurnoService.listar_turnos()[:8]
        return context


class EventosCalendarioAPIView(LoginRequiredMixin, View):
    """
    Endpoint JSON consumido por FullCalendar para cargar los eventos en tiempo real.
    """
    def get(self, request, *args, **kwargs):
        inicio = request.GET.get('start')
        fin = request.GET.get('end')
        eventos = TurnoService.eventos_calendario(inicio, fin)
        return JsonResponse(eventos, safe=False)


class CrearTurnoView(LoginRequiredMixin, CreateView):
    """
    Registra un nuevo turno y envía la confirmación por correo al dueño.
    Soporta peticiones normales y envíos asíncronos vía AJAX desde el modal.
    """
    model = Turno
    form_class = TurnoForm
    template_name = 'turnos/formulario_turno.html'
    success_url = reverse_lazy('calendario_turnos')

    def form_valid(self, form):
        turno = TurnoService.crear_turno(form)

        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'ok': True,
                'mensaje': f'¡Turno agendado con éxito para {turno.mascota.nombre}!',
                'notificado_email': turno.notificado_email,
                'email': turno.mascota.dueño.email,
            })

        if turno.notificado_email:
            messages.success(
                self.request,
                f"Turno registrado y correo de confirmación enviado a {turno.mascota.dueño.email}."
            )
        else:
            messages.warning(
                self.request,
                "Turno registrado. No se pudo enviar el correo de confirmación o el cliente no posee email."
            )

        return redirect(self.success_url)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'ok': False,
                'errores': form.errors.get_json_data()
            }, status=400)
        return super().form_invalid(form)


class CancelarTurnoView(LoginRequiredMixin, View):
    """
    Cancela un turno desde el calendario o lista.
    """
    def post(self, request, pk, *args, **kwargs):
        TurnoService.cancelar_turno(pk)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': True, 'mensaje': 'Turno cancelado correctamente.'})
        messages.info(request, "El turno ha sido cancelado.")
        return redirect('calendario_turnos')


class CambiarEstadoTurnoView(LoginRequiredMixin, View):
    """
    Permite cambiar el estado de un turno (Confirmar / Atender / Pendiente).
    """
    def post(self, request, pk, *args, **kwargs):
        nuevo_estado = request.POST.get('nuevo_estado')
        turno = TurnoService.cambiar_estado(pk, nuevo_estado)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'ok': True,
                'estado': turno.estado,
                'estado_nombre': turno.get_estado_display()
            })
        return redirect('calendario_turnos')


class IngresarSalaEsperaView(LoginRequiredMixin, View):
    """
    Realiza el check-in del paciente con turno y genera la preconsulta
    en la Sala de Espera Virtual del médico automáticamente.
    """
    def post(self, request, pk, *args, **kwargs):
        try:
            consulta, creado = TurnoService.dar_ingreso_consultorio(pk)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'ok': True,
                    'mensaje': f'¡Paciente {consulta.mascota.nombre} ingresado a la Sala de Espera médica (Consulta #{consulta.id})!',
                    'consulta_id': consulta.id,
                    'creado': creado,
                    'estado': Turno.Estado.ATENDIDO,
                    'estado_nombre': 'Atendido'
                })
            messages.success(
                request,
                f"¡Paciente {consulta.mascota.nombre} ingresado a la Sala de Espera médica con éxito!"
            )
        except Exception as e:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': str(e)}, status=400)
            messages.error(request, f"Error al ingresar paciente: {str(e)}")

        return redirect('calendario_turnos')

