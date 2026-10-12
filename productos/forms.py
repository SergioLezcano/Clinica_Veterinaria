from decimal import Decimal
from django import forms
from .models import Producto


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'categoria', 'precio_unitario', 'cantidad', 'activo']
        labels = {
            'nombre': 'Nombre del Producto / Medicamento',
            'categoria': 'Categoría',
            'precio_unitario': 'Precio Unitario ($)',
            'cantidad': 'Stock Disponible (Unidades)',
            'activo': 'Producto Activo para Venta y Aplicación',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Ej. Amoxicilina 500mg, Pipeta Antipulgas, Vacuna Antirrábica...',
                'autocomplete': 'off',
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00',
            }),
            'cantidad': forms.NumberInput(attrs={
                'min': '0',
                'placeholder': '0',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Excluimos HONORARIOS del formulario de carga física
        categorias_fisicas = [
            (c.value, c.label) for c in Producto.Categoria if c != Producto.Categoria.HONORARIOS
        ]
        self.fields['categoria'].choices = categorias_fisicas

    def clean_precio_unitario(self):
        precio = self.cleaned_data.get('precio_unitario')
        if precio is not None and precio <= Decimal('0.00'):
            raise forms.ValidationError("El precio unitario debe ser mayor a cero.")
        return precio

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad is not None and cantidad < 0:
            raise forms.ValidationError("El stock inicial no puede ser negativo.")
        return cantidad


class AjustarStockForm(forms.Form):
    MODOS = [
        ('agregar', '➕ Sumar al stock actual (Ingreso de mercadería)'),
        ('establecer', '🎯 Fijar stock exacto (Conteo de inventario)'),
    ]

    modo = forms.ChoiceField(
        choices=MODOS,
        initial='agregar',
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    cantidad = forms.IntegerField(
        min_value=1,
        label="Cantidad de unidades",
        widget=forms.NumberInput(attrs={
            'min': '1',
            'placeholder': 'Ej. 10',
            'class': 'form-input',
        })
    )
