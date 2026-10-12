from django.urls import path
from . import views

urlpatterns = [
    path('', views.CalendarioTurnosView.as_view(), name='calendario_turnos'),
    path('api/eventos/', views.EventosCalendarioAPIView.as_view(), name='api_eventos_turnos'),
    path('nuevo/', views.CrearTurnoView.as_view(), name='crear_turno'),
    path('cancelar/<int:pk>/', views.CancelarTurnoView.as_view(), name='cancelar_turno'),
    path('cambiar-estado/<int:pk>/', views.CambiarEstadoTurnoView.as_view(), name='cambiar_estado_turno'),
    path('ingreso/<int:pk>/', views.IngresarSalaEsperaView.as_view(), name='ingresar_sala_espera'),
]
