from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone


NEWS = _("News")
EVENTS = _("Event")

POST = (
    (NEWS, _("News")),
    (EVENTS, _("Event")),
)

FIRST = _("First")
SECOND = _("Second")
THIRD = _("Third")

SEMESTER = (
    (FIRST, _("First")),
    (SECOND, _("Second")),
    (THIRD, _("Third")),
)


class NewsAndEventsQuerySet(models.query.QuerySet):
    def search(self, query):
        lookups = (
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(posted_as__icontains=query)
        )
        return self.filter(lookups).distinct()


class NewsAndEventsManager(models.Manager):
    def get_queryset(self):
        return NewsAndEventsQuerySet(self.model, using=self._db)

    def all(self):
        return self.get_queryset()

    def get_by_id(self, id):
        qs = self.get_queryset().filter(
            id=id
        )  # NewsAndEvents.objects == self.get_queryset()
        if qs.count() == 1:
            return qs.first()
        return None

    def search(self, query):
        return self.get_queryset().search(query)


class NewsAndEvents(models.Model):
    title = models.CharField(max_length=200, null=True)
    summary = models.TextField(max_length=200, blank=True, null=True)
    posted_as = models.CharField(choices=POST, max_length=10)
    updated_date = models.DateTimeField(auto_now=True, auto_now_add=False, null=True)
    upload_time = models.DateTimeField(auto_now=False, auto_now_add=True, null=True)

    objects = NewsAndEventsManager()

    def __str__(self):
        return f"{self.title}"


class Session(models.Model):
    session = models.CharField(max_length=200, unique=True)
    is_current_session = models.BooleanField(default=False, blank=True, null=True)
    next_session_begins = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.session}"


class Semester(models.Model):
    semester = models.CharField(max_length=10, choices=SEMESTER, blank=True)
    is_current_semester = models.BooleanField(default=False, blank=True, null=True)
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, blank=True, null=True
    )
    next_semester_begins = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.semester}"


class ActivityLog(models.Model):
    message = models.TextField()
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.created_at}]{self.message}"


class Cotizacion(models.Model):
    ESTADO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('aceptado', 'Aceptado'),
        ('rechazado', 'Rechazado'),
    )
    
    MODALIDAD_CHOICES = [
        ('presencial', 'Presencial'),
        ('virtual', 'Virtual'),
        ('hibrido', 'Híbrido'),
    ]
    
    MODALIDAD_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('credito', 'Crédito'),
    ]
    
    # Información básica
    nombre_anio = models.CharField(max_length=100, verbose_name="Nombre del Año", null=True, blank=True)
    cotizacion = models.CharField(max_length=50, null=True, blank=True, verbose_name="Número de Cotización")
    tipo_cotizacion = models.CharField(max_length=200, verbose_name="Tipo de Cotización", null=True, blank=True)
    fecha_cotizacion = models.DateField(verbose_name="Fecha de Cotización", null=True, blank=True)
    validez_cotizacion = models.DateField(verbose_name="Validez de Cotización", null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name="Estado")
    
    # Información del cliente
    dirigido_a = models.CharField(max_length=200, verbose_name="Dirigido a", null=True, blank=True)
    empresa = models.CharField(max_length=200, verbose_name="Empresa", null=True, blank=True)
    ruc = models.CharField(max_length=20, verbose_name="RUC", null=True, blank=True)
    
    # Información del servicio
    servicio = models.TextField(verbose_name="Descripción del Servicio", null=True, blank=True)
    modalidad = models.CharField(max_length=20, choices=MODALIDAD_CHOICES, verbose_name="Modalidad", null=True, blank=True)
    sede_servicio = models.CharField(max_length=200, verbose_name="Sede del Servicio", null=True, blank=True)
    fecha_servicio = models.DateField(verbose_name="Fecha del Servicio", null=True, blank=True)
    tiempo_entrega = models.CharField(max_length=100, verbose_name="Tiempo de Entrega", null=True, blank=True)
    modalidad_pago = models.CharField(max_length=20, choices=MODALIDAD_PAGO_CHOICES, verbose_name="Modalidad de Pago", null=True, blank=True)
    
    # Campos del sistema
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Monto Total")
    creado_por = models.ForeignKey('accounts.User', on_delete=models.CASCADE, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre_anio} - {self.empresa}"

    def clean(self):
        # Validar fechas
        if self.validez_cotizacion and self.fecha_cotizacion:
            if self.validez_cotizacion <= self.fecha_cotizacion:
                raise ValidationError({
                    'validez_cotizacion': 'La validez debe ser posterior a la fecha de cotización'
                })
        
        if self.fecha_servicio and self.fecha_cotizacion:
            if self.fecha_servicio <= self.fecha_cotizacion:
                raise ValidationError({
                    'fecha_servicio': 'La fecha de servicio debe ser posterior a la fecha de cotización'
                })
        
        # Validar RUC (solo si se proporciona)
        if self.ruc:
            if not self.ruc.isdigit() or len(self.ruc) != 11:
                raise ValidationError({
                    'ruc': 'El RUC debe contener 11 dígitos numéricos'
                })
        
        # Validar monto total
        if self.monto_total < 0:
            raise ValidationError({
                'monto_total': 'El monto total no puede ser negativo'
            })

    class Meta:
        verbose_name = "Cotización"
        verbose_name_plural = "Cotizaciones"
        ordering = ['-fecha_creacion']


class ItemCotizacion(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='items')
    curso = models.CharField(max_length=200, verbose_name="Curso", null=True, blank=True)
    duracion = models.CharField(max_length=100, verbose_name="Duración", null=True, blank=True)
    descripcion = models.TextField(verbose_name="Descripción", null=True, blank=True)
    cantidad = models.IntegerField(default=1, verbose_name="Cantidad")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Unitario")
    
    def __str__(self):
        return f"{self.curso} - {self.cantidad} x {self.precio_unitario}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        # Validar cantidad
        if self.cantidad in [None, '']:
            raise ValidationError({'cantidad': 'La cantidad es obligatoria'})
        if self.cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a 0'})
        if self.cantidad > 100:
            raise ValidationError({'cantidad': 'La cantidad no puede ser mayor a 100'})
        # Validar precio unitario
        if self.precio_unitario in [None, '']:
            raise ValidationError({'precio_unitario': 'El precio unitario es obligatorio'})
        if self.precio_unitario <= 0:
            raise ValidationError({'precio_unitario': 'El precio unitario debe ser mayor a 0'})
    
    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario
    
    class Meta:
        verbose_name = "Item de cotización"
        verbose_name_plural = "Items de cotización"


class HistorialEstado(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='historial_estados')
    estado_anterior = models.CharField(max_length=20)
    estado_nuevo = models.CharField(max_length=20)
    usuario = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    comentario = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Historial de Estado"
        verbose_name_plural = "Historial de Estados"
        ordering = ['-fecha_cambio']
    
    def __str__(self):
        return f"{self.cotizacion} - {self.estado_anterior} -> {self.estado_nuevo}"
