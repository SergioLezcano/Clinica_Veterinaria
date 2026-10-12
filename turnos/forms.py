from django import forms
from django.utils import timezone
from .models import Turno
from gestion_veterinaria.models import Mascota


class TurnoForm(forms.ModelForm):
    class Meta:
        model = Turno
        fields = ['mascota', 'fecha_hora', 'motivo', 'estado', 'observaciones']
        widgets = {
            'fecha_hora': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-input',
                },
                format='%Y-%m-%dT%H:%M'
            ),
            'motivo': forms.Textarea(
                attrs={
                    'rows': 3,
                    'placeholder': 'Ej. Control de rutina, vacunación, desparasitación, decaimiento...',
                    'class': 'form-textarea'
                }
            ),
            'observaciones': forms.Textarea(
                attrs={
                    'rows': 2,
                    'placeholder': 'Indicaciones previas, ayuno o notas adicionales (opcional)',
                    'class': 'form-textarea'
                }
            ),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'mascota': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'mascota': 'Paciente (Mascota)',
            'fecha_hora': 'Fecha y Hora del Turno',
            'motivo': 'Motivo de la Consulta',
            'estado': 'Estado Inicial',
            'observaciones': 'Observaciones (Opcional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optimizamos la consulta con select_related y ordenamos alfabéticamente
        self.fields['mascota'].queryset = Mascota.objects.select_related('dueño').order_by('nombre')
        # Formato de entrada para datetime-local
        self.fields['fecha_hora'].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M']

    def clean_fecha_hora(self):
        fecha_hora = self.cleaned_data.get('fecha_hora')
        if fecha_hora and fecha_hora < timezone.now():
            raise forms.ValidationError("La fecha y hora del turno debe ser posterior al momento actual.")
        return fecha_hora
