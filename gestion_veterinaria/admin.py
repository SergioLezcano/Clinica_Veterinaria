from django.contrib import admin
from .models import Dueño, Mascota, HistoriaClinica, PerfilUsuario

admin.site.register(Dueño)
admin.site.register(Mascota)
admin.site.register(HistoriaClinica)
admin.site.register(PerfilUsuario)