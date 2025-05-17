from django.core.management.base import BaseCommand
from accounts.models import Student

def clean_students():
    # Eliminar solo los estudiantes
    Student.objects.all().delete()
    print("Tabla de estudiantes limpiada exitosamente.")

if __name__ == "__main__":
    clean_students() 