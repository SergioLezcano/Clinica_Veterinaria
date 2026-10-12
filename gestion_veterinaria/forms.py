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
        fields = ['nombre', 'especie', 'raza', 'sexo', 'fecha_nacimiento', 'dueño']
        
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
            'peso': forms.NumberInput(attrs={'step': '0.1', 'placeholder': '(en kg)'}),
            'temperatura': forms.NumberInput(attrs={'step': '0.1', 'placeholder': '(en °C)'}),
            'diagnostico': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describa el diagnóstico clínico del paciente...'}),
            'tratamiento': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Indique medicamentos, dosis y frecuencia...'}),
            'observaciones': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Notas adicionales o recordatorios'}),
        }


from django.contrib.auth.forms import SetPasswordForm

# FORMULARIO DE ALTA NUEVO USUARIO OPERADOR

class RegistroOperadorForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        label="Correo Electrónico",
        widget=forms.EmailInput(attrs={'placeholder': 'operador@ejemplo.com'}),
        help_text="Se enviará a este correo la confirmación de alta con el enlace para configurar la contraseña."
    )
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'Opcional (se creará desde el email)'}),
        label="Contraseña Inicial (Opcional)",
        help_text="Opcional. Si se deja en blanco, el operador creará su contraseña mediante el enlace enviado a su correo."
    )
    confirmar_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'Repetir contraseña si ingresó una'}),
        label="Confirmar Contraseña"
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        labels = {
            'username': 'Nombre de Usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo Electrónico'
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe un usuario registrado con este correo electrónico.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirmar_password = cleaned_data.get("confirmar_password")

        if password or confirmar_password:
            if password != confirmar_password:
                raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data


class EstablecerPasswordCustomForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({
            'placeholder': 'Ingresá tu nueva contraseña',
            'autocomplete': 'new-password'
        })
        self.fields['new_password1'].label = "Nueva Contraseña"
        self.fields['new_password2'].widget.attrs.update({
            'placeholder': 'Repetí tu nueva contraseña',
            'autocomplete': 'new-password'
        })
        self.fields['new_password2'].label = "Confirmar Nueva Contraseña"