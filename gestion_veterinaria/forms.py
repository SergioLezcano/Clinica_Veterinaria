from django import forms
from .models import Mascota, HistoriaClinica
from django.contrib.auth.models import User
from .models import PerfilUsuario

# ==========================================
# 🐾 FORMULARIO DE ALTA DE MASCOTA
# ==========================================
class MascotaForm(forms.ModelForm):
    class Meta:
        model = Mascota
        fields = ['nombre', 'especie', 'raza', 'fecha_nacimiento', 'dueño']
        
        widgets = {
            'fecha_nacimiento': forms.DateInput(
                attrs={'type': 'date', 'class': 'input-calendario'}
            ),
        }


# ==========================================
# 📥 FORMULARIO DE PRECONSULTA (OPERADOR)
# ==========================================
class PreConsultaForm(forms.ModelForm):
    class Meta:
        model = HistoriaClinica
        fields = ['mascota', 'motivo'] 
        widgets = {
            'motivo': forms.Textarea(attrs={'rows': 3, 'placeholder': '¿Por qué viene hoy?'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si hay un dato inicial para mascota (viene desde el botón)
        if 'initial' in kwargs and 'mascota' in kwargs['initial']:
            # Opción A: Podés deshabilitarlo para que no lo alteren por error
            self.fields['mascota'].widget.attrs['disabled'] = 'disabled'
            # Es necesario por seguridad, ya que los campos 'disabled' no se envían en el POST
            self.fields['mascota'].required = False


# ==========================================
# 🩺 FORMULARIO DE CIERRE CLÍNICO (MÉDICO)
# ==========================================
class CierreConsultaForm(forms.ModelForm):
    class Meta:
        model = HistoriaClinica
        fields = ['peso', 'temperatura', 'diagnostico', 'tratamiento', 'observaciones']
        widgets = {
            'peso': forms.NumberInput(attrs={'step': '0.1', 'placeholder': 'kg'}),
            'temperatura': forms.NumberInput(attrs={'step': '0.1', 'placeholder': '°C'}),
            'diagnostico': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Hallazgos clínicos...'}),
            'tratamiento': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Medicamentos y dosis...'}),
            'observaciones': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Otros datos de interés...'}),
        }


# FORMULARIO DE ALTA NUEVO USUARIO OPERADOR

class RegistroOperadorForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Contraseña segura'}), label="Contraseña")
    confirmar_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Repetir contraseña'}), label="Confirmar Contraseña")
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        labels = {
            'username': 'Nombre de Usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo Electrónico'
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirmar_password = cleaned_data.get("confirmar_password")

        if password != confirmar_password:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data