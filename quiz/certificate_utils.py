"""
Utilidades para el manejo de certificados
Funciones unificadas para lógica de fechas y estados
"""
from datetime import date, timedelta, datetime


def datetime_to_date(dt):
    """Convertir datetime a date de forma segura"""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.date()
    return dt


def is_certificate_active(certificate, hoy):
    """
    Determinar si un certificado está activo (no vencido)
    
    Args:
        certificate: Objeto Sitting (automático) o ManualCertificate (manual)
        hoy: Fecha actual (date)
    
    Returns:
        bool: True si el certificado está activo
    """
    if hasattr(certificate, 'fecha_aprobacion'):  # Certificado automático
        if certificate.fecha_aprobacion:
            fecha_aprobacion = datetime_to_date(certificate.fecha_aprobacion)
            return fecha_aprobacion >= hoy - timedelta(days=365)
        return False
    else:  # Certificado manual
        return certificate.fecha_vencimiento >= hoy


def is_certificate_expired(certificate, hoy):
    """
    Determinar si un certificado está vencido
    
    Args:
        certificate: Objeto Sitting (automático) o ManualCertificate (manual)
        hoy: Fecha actual (date)
    
    Returns:
        bool: True si el certificado está vencido
    """
    if hasattr(certificate, 'fecha_aprobacion'):  # Certificado automático
        if certificate.fecha_aprobacion:
            fecha_aprobacion = datetime_to_date(certificate.fecha_aprobacion)
            return fecha_aprobacion < hoy - timedelta(days=365)
        return True
    else:  # Certificado manual
        return certificate.fecha_vencimiento < hoy


def is_certificate_expiring_soon(certificate, hoy, days=30):
    """
    Determinar si un certificado está por vencer
    
    Args:
        certificate: Objeto Sitting (automático) o ManualCertificate (manual)
        hoy: Fecha actual (date)
        days: Días de anticipación para considerar "por vencer" (default: 30)
    
    Returns:
        bool: True si el certificado está por vencer
    """
    if hasattr(certificate, 'fecha_aprobacion'):  # Certificado automático
        if certificate.fecha_aprobacion:
            fecha_aprobacion = datetime_to_date(certificate.fecha_aprobacion)
            fecha_vencimiento = fecha_aprobacion + timedelta(days=365)
            return hoy <= fecha_vencimiento <= hoy + timedelta(days=days)
        return False
    else:  # Certificado manual
        return (certificate.activo and 
               hoy < certificate.fecha_vencimiento <= hoy + timedelta(days=days))


def get_certificate_expiration_date(certificate):
    """
    Obtener la fecha de vencimiento de un certificado
    
    Args:
        certificate: Objeto Sitting (automático) o ManualCertificate (manual)
    
    Returns:
        date: Fecha de vencimiento del certificado
    """
    if hasattr(certificate, 'fecha_aprobacion'):  # Certificado automático
        if certificate.fecha_aprobacion:
            fecha_aprobacion = datetime_to_date(certificate.fecha_aprobacion)
            return fecha_aprobacion + timedelta(days=365)
        return None
    else:  # Certificado manual
        return certificate.fecha_vencimiento


def get_certificate_status(certificate, hoy):
    """
    Obtener el estado completo de un certificado
    
    Args:
        certificate: Objeto Sitting (automático) o ManualCertificate (manual)
        hoy: Fecha actual (date)
    
    Returns:
        dict: Estado del certificado con información detallada
    """
    fecha_vencimiento = get_certificate_expiration_date(certificate)
    
    if fecha_vencimiento is None:
        return {
            'status': 'invalid',
            'is_active': False,
            'is_expired': True,
            'is_expiring_soon': False,
            'expiration_date': None,
            'days_until_expiration': None
        }
    
    is_active = is_certificate_active(certificate, hoy)
    is_expired = is_certificate_expired(certificate, hoy)
    is_expiring_soon = is_certificate_expiring_soon(certificate, hoy)
    days_until_expiration = (fecha_vencimiento - hoy).days
    
    if is_expired:
        status = 'expired'
    elif is_expiring_soon:
        status = 'expiring_soon'
    elif is_active:
        status = 'active'
    else:
        status = 'inactive'
    
    return {
        'status': status,
        'is_active': is_active,
        'is_expired': is_expired,
        'is_expiring_soon': is_expiring_soon,
        'expiration_date': fecha_vencimiento,
        'days_until_expiration': days_until_expiration
    }
