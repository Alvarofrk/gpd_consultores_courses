from django import forms
from django.forms import inlineformset_factory
from .models import NewsAndEvents, Session, Semester, SEMESTER, Cotizacion, ItemCotizacion, Evento


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_cotizacion'].required = False
        self.fields['fecha_servicio'].required = False
        self.fields['validez_cotizacion'].required = False
        if self.instance and self.instance.pk:
            if self.instance.fecha_cotizacion:
                self.fields['fecha_cotizacion'].initial = self.instance.fecha_cotizacion.strftime('%Y-%m-%d')
            if self.instance.fecha_servicio:
                self.fields['fecha_servicio'].initial = self.instance.fecha_servicio.strftime('%Y-%m-%d')
            if self.instance.validez_cotizacion:
                self.fields['validez_cotizacion'].initial = self.instance.validez_cotizacion.strftime('%Y-%m-%d')

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('fecha_cotizacion') and self.instance and self.instance.pk:
            cleaned_data['fecha_cotizacion'] = self.instance.fecha_cotizacion
        if not cleaned_data.get('fecha_servicio') and self.instance and self.instance.pk:
            cleaned_data['fecha_servicio'] = self.instance.fecha_servicio
        if not cleaned_data.get('validez_cotizacion') and self.instance and self.instance.pk:
            cleaned_data['validez_cotizacion'] = self.instance.validez_cotizacion
        return cleaned_data


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

    def clean(self):
        cleaned_data = super().clean()
        # Si todos los campos están vacíos, no validar
        if not any(cleaned_data.values()):
            return cleaned_data
        
        # Si algún campo está lleno, validar que todos los campos requeridos estén presentes
        if any(cleaned_data.values()):
            if not cleaned_data.get('cantidad'):
                self.add_error('cantidad', 'Este campo es obligatorio.')
            if not cleaned_data.get('precio_unitario'):
                self.add_error('precio_unitario', 'Este campo es obligatorio.')
            
            # Validar que la cantidad sea positiva y no exceda el límite
            cantidad = cleaned_data.get('cantidad')
            if cantidad is not None:
                if cantidad <= 0:
                    self.add_error('cantidad', 'La cantidad debe ser mayor a 0')
                elif cantidad > 100:
                    self.add_error('cantidad', 'La cantidad no puede ser mayor a 100')
            
            # Validar que el precio unitario sea positivo
            precio = cleaned_data.get('precio_unitario')
            if precio is not None and precio <= 0:
                self.add_error('precio_unitario', 'El precio unitario debe ser mayor a 0')
        
        return cleaned_data


# Formulario para el conjunto de items
ItemCotizacionFormSet = inlineformset_factory(
    Cotizacion,
    ItemCotizacion,
    form=ItemCotizacionForm,
    extra=7,
    can_delete=False,
    max_num=7,
    validate_max=True,
    fields=['curso', 'duracion', 'descripcion', 'cantidad', 'precio_unitario']
)


class EventoForm(forms.ModelForm):
    """Formulario para crear y editar eventos"""
    
    # Campo para canales de envío
    canales_envio = forms.MultipleChoiceField(
        choices=Evento.CANAL_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        help_text="Selecciona los canales para enviar recordatorios"
    )
    
    class Meta:
        model = Evento
        fields = ['titulo', 'descripcion', 'tipo', 'fecha_inicio', 'fecha_fin', 'mensaje_recordatorio', 'dias_antes', 'horas_antes', 'canales_envio', 'emails_destino', 'telefonos_destino', 'activo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título del evento'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción del evento'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'fecha_inicio': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'fecha_fin': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'mensaje_recordatorio': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'dias_antes': forms.NumberInput(attrs={'class': 'form-control'}),
            'horas_antes': forms.NumberInput(attrs={'class': 'form-control'}),
            'emails_destino': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'telefonos_destino': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer campos opcionales
        for field in ['fecha_fin', 'mensaje_recordatorio', 'dias_antes', 'horas_antes', 'emails_destino', 'telefonos_destino']:
            self.fields[field].required = False
            if hasattr(self.fields[field].widget, 'attrs'):
                self.fields[field].widget.attrs.pop('required', None)
        
        # Si es una instancia existente, establecer los valores de canales_envio
        if self.instance and self.instance.pk:
            if self.instance.canales_envio:
                self.fields['canales_envio'].initial = self.instance.canales_envio
            else:
                # Para nuevos eventos, establecer activo como True por defecto
                self.fields['activo'].initial = True
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        # Validar que la fecha de fin sea posterior a la de inicio
        if fecha_inicio and fecha_fin and fecha_fin <= fecha_inicio:
            raise forms.ValidationError("La fecha de fin debe ser posterior a la fecha de inicio.")
        
        # Validar que el recordatorio se envíe antes del inicio del evento
        dias_antes = cleaned_data.get('dias_antes', 0) or 0
        horas_antes = cleaned_data.get('horas_antes', 0) or 0
        
        # Si hay recordatorio configurado, validar que sea antes del evento
        if fecha_inicio and (dias_antes > 0 or horas_antes > 0):
            from datetime import timedelta
            tiempo_recordatorio = timedelta(days=dias_antes, hours=horas_antes)
            
            # El recordatorio debe enviarse antes del inicio del evento
            # No necesitamos validar contra la duración del evento
            # Solo verificamos que los valores sean razonables (no negativos)
            if dias_antes < 0 or horas_antes < 0:
                raise forms.ValidationError("Los días y horas antes del evento deben ser valores positivos.")
        
        return cleaned_data

    def clean_canales_envio(self):
        data = self.cleaned_data.get('canales_envio')
        if not data:
            return []
        return list(data)


class FiltroEventoForm(forms.Form):
    """Formulario para filtrar eventos en el calendario"""
    
    mes = forms.ChoiceField(
        choices=[
            (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
            (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
            (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    año = forms.ChoiceField(
        choices=[(year, year) for year in range(2024, 2030)],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    tipo = forms.ChoiceField(
        choices=[('', 'Todos los tipos')] + Evento.TIPO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Establecer mes y año actual por defecto
        from datetime import datetime
        now = datetime.now()
        self.fields['mes'].initial = now.month
        self.fields['año'].initial = now.year
