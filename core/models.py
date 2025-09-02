from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import math


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
    
    FORMA_PAGO_CHOICES = [
        ('50_50', '50% al iniciar y 50% al finalizar'),
        ('100_adelantado', '100% adelantado'),
        ('al_credito', 'Al crédito'),
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
    
    # Información de pagos
    monto_cancelado = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Monto Cancelado", help_text="Monto que ya ha sido pagado")
    
    # Campos del sistema
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Monto Total")
    creado_por = models.ForeignKey('accounts.User', on_delete=models.CASCADE, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    forma_pago = models.CharField(
        max_length=20,
        choices=FORMA_PAGO_CHOICES,
        default='100_adelantado',
        verbose_name="Forma de Pago"
    )
    plazo_credito_dias = models.IntegerField(
        null=True, blank=True,
        verbose_name="Plazo de crédito (días)",
        help_text="Plazo en días para pago al crédito"
    )
    plazo_credito_fecha = models.DateField(
        null=True, blank=True,
        verbose_name="Fecha límite de crédito",
        help_text="Fecha límite para pago al crédito"
    )

    def __str__(self):
        return f"{self.nombre_anio} - {self.empresa}"

    @property
    def total_con_igv(self):
        """Calcula el total con IGV (18%)"""
        return self.monto_total * Decimal('1.18')

    @property
    def total_con_igv_redondeado(self):
        """Calcula el total con IGV redondeado hacia arriba sin decimales"""
        total_calculado = self.monto_total * Decimal('1.18')
        return math.ceil(total_calculado)

    @property
    def detraccion(self):
        """Calcula la detracción del 12% si el total + IGV es >= 700"""
        if self.total_con_igv >= Decimal('700.00'):
            return self.total_con_igv * Decimal('0.12')
        return Decimal('0.00')

    @property
    def detraccion_redondeada(self):
        """Calcula la detracción redondeada hacia arriba sin decimales"""
        if self.total_con_igv >= Decimal('700.00'):
            detraccion_calculada = self.total_con_igv * Decimal('0.12')
            return math.ceil(detraccion_calculada)
        return Decimal('0.00')

    @property
    def total_con_detraccion(self):
        """Calcula el total final con IGV y detracción"""
        return self.total_con_igv + self.detraccion

    @property
    def total_con_detraccion_redondeado(self):
        """Calcula el total final con IGV y detracción redondeada"""
        return self.total_con_igv + self.detraccion_redondeada

    @property
    def porcentaje_cancelado(self):
        """Calcula el porcentaje cancelado del total final"""
        if self.total_con_detraccion > 0:
            return (self.monto_cancelado / self.total_con_detraccion) * 100
        return 0

    @property
    def monto_pendiente(self):
        """Calcula el monto pendiente por pagar"""
        return self.total_con_detraccion - self.monto_cancelado

    @property
    def porcentaje_pendiente(self):
        """Calcula el porcentaje pendiente por pagar"""
        return 100 - self.porcentaje_cancelado

    @property
    def igv(self):
        """Retorna el IGV calculado como la diferencia entre total_con_igv y monto_total"""
        return self.total_con_igv - self.monto_total

    @property
    def adelanto(self):
        if self.forma_pago == '50_50':
            return self.total_con_detraccion * 0.5
        elif self.forma_pago == '100_adelantado':
            return self.total_con_detraccion
        return 0

    @property
    def saldo(self):
        if self.forma_pago == '50_50':
            return self.total_con_detraccion * 0.5
        elif self.forma_pago == '100_adelantado':
            return 0
        elif self.forma_pago == 'al_credito':
            return self.total_con_detraccion
        return 0

    @property
    def porcentaje_adelanto(self):
        if self.forma_pago == '50_50':
            return 50
        elif self.forma_pago == '100_adelantado':
            return 100
        return 0

    @property
    def porcentaje_saldo(self):
        if self.forma_pago == '50_50':
            return 50
        elif self.forma_pago == '100_adelantado':
            return 0
        elif self.forma_pago == 'al_credito':
            return 100
        return 0

    # Propiedades específicas para crédito
    @property
    def fecha_vencimiento_calculada(self):
        """Calcula la fecha de vencimiento basada en el plazo"""
        if self.forma_pago != 'al_credito':
            return None
        
        if not self.fecha_cotizacion:
            return None
            
        from datetime import timedelta
        if self.plazo_credito_dias:
            return self.fecha_cotizacion + timedelta(days=self.plazo_credito_dias)
        elif self.plazo_credito_fecha:
            return self.plazo_credito_fecha
        return None

    @property
    def monto_credito(self):
        """Monto total a crédito (solo para forma_pago = 'al_credito')"""
        if self.forma_pago == 'al_credito':
            return self.total_con_detraccion
        return 0

    @property
    def monto_pendiente_credito(self):
        """Monto pendiente del crédito"""
        if self.forma_pago == 'al_credito':
            return self.total_con_detraccion - self.monto_cancelado
        return 0

    @property
    def porcentaje_pagado_credito(self):
        """Porcentaje pagado del crédito"""
        if self.forma_pago == 'al_credito' and self.total_con_detraccion > 0:
            return (self.monto_cancelado / self.total_con_detraccion) * 100
        return 0

    @property
    def dias_restantes_credito(self):
        """Días restantes hasta el vencimiento"""
        if self.forma_pago == 'al_credito' and self.fecha_vencimiento_calculada:
            from django.utils import timezone
            dias = (self.fecha_vencimiento_calculada - timezone.now().date()).days
            return max(0, dias)  # No mostrar días negativos
        return None

    @property
    def estado_credito(self):
        """Estado del crédito basado en pagos y vencimiento"""
        if self.forma_pago != 'al_credito':
            return None
        
        if self.monto_pendiente_credito == 0:
            return 'pagado'
        elif self.dias_restantes_credito is not None and self.dias_restantes_credito <= 0:
            return 'vencido'
        elif self.monto_cancelado > 0:
            return 'parcial'
        else:
            return 'pendiente'

    @property
    def esta_vencido(self):
        """Verifica si el crédito está vencido"""
        return self.forma_pago == 'al_credito' and self.dias_restantes_credito is not None and self.dias_restantes_credito <= 0

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
        
        # Validar monto cancelado (campo interno)
        if self.monto_cancelado < 0:
            raise ValidationError({
                'monto_cancelado': 'El monto cancelado no puede ser negativo'
            })
        
        # Validar forma de pago
        if self.forma_pago == 'al_credito':
            if not self.plazo_credito_dias and not self.plazo_credito_fecha:
                raise ValidationError({
                    'forma_pago': 'Para pago al crédito debe especificar un plazo en días o una fecha límite'
                })
        
        # Validar plazo de crédito
        if self.plazo_credito_dias is not None and self.plazo_credito_dias <= 0:
            raise ValidationError({
                'plazo_credito_dias': 'El plazo de crédito debe ser mayor a 0 días'
            })
        
        if self.plazo_credito_fecha and self.fecha_cotizacion:
            if self.plazo_credito_fecha <= self.fecha_cotizacion:
                raise ValidationError({
                    'plazo_credito_fecha': 'La fecha límite de crédito debe ser posterior a la fecha de cotización'
                })
        
        # Validaciones específicas para crédito
        if self.forma_pago == 'al_credito':
            # El monto cancelado no puede ser mayor al total
            if self.monto_cancelado > self.total_con_detraccion:
                raise ValidationError({
                    'monto_cancelado': 'El monto pagado no puede ser mayor al total a crédito'
                })
            
            # Validar que tenga fecha de cotización para calcular vencimiento
            if not self.fecha_cotizacion and self.plazo_credito_dias:
                raise ValidationError({
                    'fecha_cotizacion': 'Para calcular el plazo de crédito en días, debe especificar la fecha de cotización'
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


class Evento(models.Model):
    """Modelo para eventos del calendario con recordatorios automáticos"""
    
    TIPO_CHOICES = [
        ('reunion', 'Reunión'),
        ('curso', 'Curso'),
        ('examen', 'Examen'),
        ('certificado', 'Certificado'),
        ('pago', 'Pago'),
        ('otro', 'Otro'),
    ]
    
    CANAL_CHOICES = [
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram'),
        ('sms', 'SMS'),
    ]
    
    # Información básica del evento
    titulo = models.CharField(max_length=200, verbose_name="Título del Evento")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='reunion', verbose_name="Tipo de Evento")
    
    # Fecha y hora
    fecha_inicio = models.DateTimeField(verbose_name="Fecha y Hora de Inicio")
    fecha_fin = models.DateTimeField(verbose_name="Fecha y Hora de Fin", blank=True, null=True)
    
    # Configuración de recordatorios
    mensaje_recordatorio = models.TextField(verbose_name="Mensaje de Recordatorio", blank=True, null=True)
    dias_antes = models.IntegerField(default=1, verbose_name="Días antes del evento", blank=True, null=True)
    horas_antes = models.IntegerField(default=0, verbose_name="Horas antes del evento", blank=True, null=True)
    canales_envio = models.JSONField(default=list, verbose_name="Canales de Envío", blank=True, null=True)
    emails_destino = models.TextField(blank=True, null=True, verbose_name="Emails destinatarios", help_text="Separa los emails por coma, punto y coma o salto de línea.")
    telefonos_destino = models.TextField(blank=True, null=True, verbose_name="Números WhatsApp destinatarios", help_text="Incluye el código de país. Separa los números por coma o salto de línea.")
    
    # Estado del recordatorio
    recordatorio_enviado = models.BooleanField(default=False, verbose_name="Recordatorio Enviado")
    fecha_envio_recordatorio = models.DateTimeField(blank=True, null=True, verbose_name="Fecha de Envío")
    
    # Información del creador
    creado_por = models.ForeignKey('accounts.User', on_delete=models.CASCADE, verbose_name="Creado por")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Evento activo/inactivo
    activo = models.BooleanField(default=True, verbose_name="Evento Activo")
    
    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"{self.titulo} - {self.fecha_inicio.strftime('%d/%m/%Y %H:%M')}"
    
    @property
    def fecha_recordatorio(self):
        """Calcula cuándo debe enviarse el recordatorio"""
        from datetime import timedelta
        return self.fecha_inicio - timedelta(days=self.dias_antes, hours=self.horas_antes)
    
    @property
    def debe_enviar_recordatorio(self):
        """Verifica si debe enviarse el recordatorio"""
        from django.utils import timezone
        return (
            self.activo and 
            not self.recordatorio_enviado and 
            timezone.now() >= self.fecha_recordatorio and
            timezone.now() < self.fecha_inicio
        )
    
    def marcar_recordatorio_enviado(self):
        """Marca el recordatorio como enviado"""
        from django.utils import timezone
        self.recordatorio_enviado = True
        self.fecha_envio_recordatorio = timezone.now()
        self.save()


class LogRecordatorio(models.Model):
    """Log de recordatorios enviados"""
    
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='logs_recordatorio')
    canal = models.CharField(max_length=20, choices=Evento.CANAL_CHOICES)
    destinatario = models.CharField(max_length=200, verbose_name="Destinatario")
    mensaje = models.TextField(verbose_name="Mensaje Enviado")
    enviado_exitosamente = models.BooleanField(default=True, verbose_name="Enviado Exitosamente")
    error_mensaje = models.TextField(blank=True, null=True, verbose_name="Mensaje de Error")
    fecha_envio = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Log de Recordatorio"
        verbose_name_plural = "Logs de Recordatorios"
        ordering = ['-fecha_envio']
    
    def __str__(self):
        return f"{self.evento.titulo} - {self.canal} - {self.fecha_envio.strftime('%d/%m/%Y %H:%M')}"
