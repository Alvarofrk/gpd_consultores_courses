from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import Session, Semester, NewsAndEvents, Evento, LogRecordatorio


class NewsAndEventsAdmin(TranslationAdmin):
    pass


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo', 'fecha_inicio', 'fecha_fin', 'creado_por', 'activo', 'recordatorio_enviado']
    list_filter = ['tipo', 'activo', 'recordatorio_enviado', 'fecha_inicio', 'creado_por']
    search_fields = ['titulo', 'descripcion', 'mensaje_recordatorio']
    date_hierarchy = 'fecha_inicio'
    ordering = ['-fecha_inicio']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('titulo', 'descripcion', 'tipo', 'activo')
        }),
        ('Fecha y Hora', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
        ('Configuración de Recordatorios', {
            'fields': ('mensaje_recordatorio', 'dias_antes', 'horas_antes', 'canales_envio', 'emails_destino', 'telefonos_destino')
        }),
        ('Estado del Recordatorio', {
            'fields': ('recordatorio_enviado', 'fecha_envio_recordatorio'),
            'classes': ('collapse',)
        }),
        ('Información del Sistema', {
            'fields': ('creado_por', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo evento
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('creado_por')


@admin.register(LogRecordatorio)
class LogRecordatorioAdmin(admin.ModelAdmin):
    list_display = ['evento', 'canal', 'destinatario', 'enviado_exitosamente', 'fecha_envio']
    list_filter = ['canal', 'enviado_exitosamente', 'fecha_envio']
    search_fields = ['evento__titulo', 'destinatario', 'mensaje']
    date_hierarchy = 'fecha_envio'
    ordering = ['-fecha_envio']
    readonly_fields = ['fecha_envio']
    
    fieldsets = (
        ('Información del Envío', {
            'fields': ('evento', 'canal', 'destinatario', 'fecha_envio')
        }),
        ('Contenido del Mensaje', {
            'fields': ('mensaje',)
        }),
        ('Estado del Envío', {
            'fields': ('enviado_exitosamente', 'error_mensaje')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('evento')


admin.site.register(Semester)
admin.site.register(Session)
admin.site.register(NewsAndEvents, NewsAndEventsAdmin)
