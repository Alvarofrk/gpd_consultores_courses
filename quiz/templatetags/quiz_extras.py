from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiplica el valor por el argumento"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def add_days(value, days):
    """Añade días a una fecha"""
    try:
        return value + timedelta(days=int(days))
    except (ValueError, TypeError):
        return value 