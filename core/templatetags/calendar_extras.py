from django import template
import math

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Filtro para obtener un elemento de un diccionario por clave"""
    return dictionary.get(key)

@register.filter
def ceil1(value):
    try:
        return math.ceil(float(value) * 10) / 10
    except (ValueError, TypeError):
        return value 