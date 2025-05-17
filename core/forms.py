from django import forms
from django.forms import inlineformset_factory
from .models import NewsAndEvents, Session, Semester, SEMESTER, Cotizacion, ItemCotizacion


# news and events
class NewsAndEventsForm(forms.ModelForm):
    class Meta:
        model = NewsAndEvents
        fields = (
            "title",
            "summary",
            "posted_as",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update({"class": "form-control"})
        self.fields["summary"].widget.attrs.update({"class": "form-control"})
        self.fields["posted_as"].widget.attrs.update({"class": "form-control"})


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ("session", "is_current_session")


class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ("semester", "is_current_semester")


class CotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion
        fields = [
            # Información básica
            'nombre_anio',
            'cotizacion',
            'tipo_cotizacion',
            'fecha_cotizacion',
            'validez_cotizacion',
            'estado',
            
            # Información del cliente
            'dirigido_a',
            'empresa',
            'ruc',
            
            # Información del servicio
            'servicio',
            'modalidad',
            'sede_servicio',
            'fecha_servicio',
            'tiempo_entrega',
            'modalidad_pago',
        ]
        widgets = {
            'fecha_cotizacion': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'validez_cotizacion': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_servicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'modalidad': forms.Select(attrs={'class': 'form-control'}),
            'modalidad_pago': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'tipo_cotizacion': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ItemCotizacionForm(forms.ModelForm):
    class Meta:
        model = ItemCotizacion
        fields = ['curso', 'duracion', 'descripcion', 'cantidad', 'precio_unitario']
        widgets = {
            'curso': forms.TextInput(attrs={'class': 'form-control'}),
            'duracion': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control cantidad',
                'min': '1',
                'step': '1',
                'type': 'number'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control precio',
                'min': '0',
                'step': '0.01',
                'type': 'number'
            }),
        }


# Formulario para el conjunto de items
ItemCotizacionFormSet = inlineformset_factory(
    Cotizacion,
    ItemCotizacion,
    form=ItemCotizacionForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
    max_num=10,
    validate_max=True,
    fields=['curso', 'duracion', 'descripcion', 'cantidad', 'precio_unitario']
)
