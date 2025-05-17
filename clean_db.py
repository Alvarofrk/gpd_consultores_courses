from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from course.models import Course, Program
from accounts.models import Student, Parent, DepartmentHead
from quiz.models import Quiz
from core.models import NewsAndEvents, Session

def clean_database():
    # Mantener el superusuario
    User = get_user_model()
    superuser = User.objects.filter(is_superuser=True).first()
    
    # Eliminar datos de cursos
    Course.objects.all().delete()
    Program.objects.all().delete()
    
    # Eliminar datos de usuarios (excepto superusuario)
    Student.objects.all().delete()
    Parent.objects.all().delete()
    DepartmentHead.objects.all().delete()
    User.objects.exclude(id=superuser.id if superuser else None).delete()
    
    # Eliminar datos de quiz
    Quiz.objects.all().delete()
    
    # Eliminar datos del core
    NewsAndEvents.objects.all().delete()
    Session.objects.all().delete()
    
    print("Base de datos limpiada exitosamente. El superusuario se mantiene.")

if __name__ == "__main__":
    clean_database() 