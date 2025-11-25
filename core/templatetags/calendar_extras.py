from django import template
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Filtro para obtener un elemento de un diccionario por clave"""
    return dictionary.get(key)


@register.filter
def ceil1(value):
    """
    Redondea a dos decimales usando el método estándar (ROUND_HALF_UP).
    Se mantiene el nombre del filtro por compatibilidad con las plantillas existentes.
    """
    try:
        decimal_value = Decimal(str(value))
        return decimal_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        return value