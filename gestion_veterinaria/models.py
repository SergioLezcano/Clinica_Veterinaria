from django.db import models
from django.contrib.auth.models import User
from datetime import date

class Dueño(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"

class Mascota(models.Model):
    class Sexo(models.TextChoices):
        MACHO = 'M', 'Macho'
        HEMBBRA = 'H', 'Hembra'

    dueño = models.ForeignKey(Dueño, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=50)
    especie = models.CharField(max_length=50)
    raza = models.CharField(max_length=50)
    sexo = models.CharField(max_length=10, choices=Sexo.choices)
    fecha_nacimiento = models.DateField(null=True, blank=True)

    # Propiedad que Calcula la edad en tiempo real
    @property
    def edad(self):
        if not self.fecha_nacimiento:
            return "No especificada"
        
        hoy = date.today()
        # Calculamos la diferencia en años
        anios = hoy.year - self.fecha_nacimiento.year - ((hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
        
        if anios < 1:
            # Si tiene menos de un año, calculamos los meses aproximados
            meses = (hoy.year - self.fecha_nacimiento.year) * 12 + hoy.month - self.fecha_nacimiento.month
            if meses == 0:
                return "Menos de un mes"
            return f"{meses} {'mes' if meses == 1 else 'meses'}"
        
        return f"{anios} {'año' if anios == 1 else 'años'}"

    def __str__(self):
        return f"{self.nombre} ({self.dueño.apellido})"

class HistoriaClinica(models.Model):
    # El "Semáforo" de atención
    ESTADO_CHOICES = [('P', 'Pendiente'), ('C', 'Completada'), ('X', 'Cancelada')]

    # Campos iniciales (Operador)
    mascota = models.ForeignKey(Mascota, on_delete=models.CASCADE)
    fecha_consulta = models.DateTimeField(auto_now_add=True)
    motivo = models.TextField()

    # Campos clínicos (Médico)
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    temperatura = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    diagnostico = models.TextField(null=True, blank=True)
    tratamiento = models.TextField(null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)
    
    estado = models.CharField(max_length=1, choices=ESTADO_CHOICES, default='P')

    def __str__(self):
        return f"Consulta {self.mascota.nombre} - {self.fecha_consulta.date()}"

# --- SECCIÓN DE USUARIOS Y ROLES ---

class PerfilUsuario(models.Model):
    class Rol(models.TextChoices):
        ADMINISTRADOR = 'ADMIN', 'Administrador'
        OPERADOR = 'OPER', 'Operador'

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rol = models.CharField(max_length=10, choices=Rol.choices, default=Rol.OPERADOR)

    def __str__(self):
        return f"{self.user.username} - {self.rol}"