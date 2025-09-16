from datetime import datetime
import re
from django.utils.text import slugify
from django.db import models


def generate_next_cotization_number():
    """
    Genera el siguiente número de cotización automáticamente
    Patrón: COTIZACIÓN NRO. {número}-{año}-{sufijo}
    
    Ejemplo:
    - Última: COTIZACIÓN NRO. 433-2025-GC
    - Nueva:  COTIZACIÓN NRO. 434-2025-GC
    """
    from .models import Cotizacion
    
    current_year = datetime.now().year
    suffix = "GC"  # Sufijo fijo
    
    # Buscar la última cotización del año actual
    last_cotization = Cotizacion.objects.filter(
        cotizacion__icontains=f"-{current_year}-{suffix}"
    ).order_by('-fecha_creacion').first()
    
    if last_cotization and last_cotization.cotizacion:
        # Extraer número de la última cotización usando regex
        pattern = r'COTIZACIÓN NRO\. (\d+)-' + str(current_year) + '-' + suffix
        match = re.search(pattern, last_cotization.cotizacion)
        
        if match:
            last_number = int(match.group(1))
            next_number = last_number + 1
        else:
            # Si no coincide el patrón, empezar desde 1
            next_number = 1
    else:
        # Si no hay cotizaciones del año actual, empezar desde 1
        next_number = 1
    
    return f"COTIZACIÓN NRO. {next_number}-{current_year}-{suffix}"


def extract_cotization_number(cotization_string):
    """
    Extrae el número de una cotización existente
    Útil para validaciones y comparaciones
    """
    if not cotization_string:
        return None
    
    pattern = r'COTIZACIÓN NRO\. (\d+)-(\d+)-(\w+)'
    match = re.search(pattern, cotization_string)
    
    if match:
        return {
            'number': int(match.group(1)),
            'year': int(match.group(2)),
            'suffix': match.group(3)
        }
    return None


def validate_cotization_format(cotization_string):
    """
    Valida que el formato de la cotización sea correcto
    """
    if not cotization_string:
        return False
    
    pattern = r'^COTIZACIÓN NRO\. \d+-\d{4}-[A-Z]{2}$'
    return bool(re.match(pattern, cotization_string))


def unique_slug_generator(instance, new_slug=None):
    """
    Generador de slugs únicos para modelos Django
    Función existente que se importa desde otros módulos
    """
    if new_slug is not None:
        slug = new_slug
    else:
        slug = slugify(instance.title)
    
    Klass = instance.__class__
    qs_exists = Klass.objects.filter(slug=slug).exists()
    if qs_exists:
        new_slug = "{slug}-{randstr}".format(
            slug=slug,
            randstr=re.sub(r'[^a-zA-Z0-9]', '', str(instance.id))[:5]
        )
        return unique_slug_generator(instance, new_slug=new_slug)
    return slug


def send_html_email(subject, recipient_list, template, context):
    """
    Función para enviar emails HTML
    Implementación básica para compatibilidad
    """
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.conf import settings
    
    try:
        html_message = render_to_string(template, context)
        send_mail(
            subject=subject,
            message='',  # Versión de texto plano vacía
            html_message=html_message,
            from_email=settings.EMAIL_FROM_ADDRESS,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error enviando email: {e}")
        return False