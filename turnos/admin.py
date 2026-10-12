from django.contrib import admin
from .models import Turno


@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ('id', 'mascota', 'fecha_hora', 'estado', 'notificado_email')
    list_filter = ('estado', 'notificado_email', 'fecha_hora')
    search_fields = ('mascota__nombre', 'mascota__dueño__apellido', 'mascota__dueño__email', 'motivo')
    date_hierarchy = 'fecha_hora'
