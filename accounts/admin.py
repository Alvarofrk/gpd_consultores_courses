from django.contrib import admin
from django.utils.html import format_html
from .models import User, Student, Parent

class StudentInline(admin.StackedInline):
    model = Student
    extra = 1
    fields = ('level', 'program', 'cargo', 'empresa', 'courses')

class UserAdmin(admin.ModelAdmin):
    list_display = [
        "get_full_name",
        "username",
        "email",
        "is_active",
        "is_student",
        "is_lecturer",
        "is_parent",
        "is_staff",
        "get_student_info"
    ]
    search_fields = [
        "username",
        "first_name",
        "last_name",
        "email",
    ]
    list_filter = [
        "is_active",
        "is_student",
        "is_lecturer",
        "is_parent",
        "is_staff",
    ]
    inlines = [StudentInline]
    
    def get_student_info(self, obj):
        if obj.is_student:
            try:
                student = obj.student
                return format_html(
                    '<span style="color: green;">Nivel: {} - Programa: {}</span>',
                    student.level,
                    student.program
                )
            except:
                return format_html('<span style="color: red;">No tiene datos de estudiante</span>')
        return "-"
    get_student_info.short_description = "Información del Estudiante"

class StudentAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "level",
        "program",
        "cargo",
        "empresa",
        "get_assigned_courses"
    ]
    search_fields = [
        "student__username",
        "student__first_name",
        "student__last_name",
        "program__title",
    ]
    list_filter = [
        "level",
        "program",
    ]
    filter_horizontal = ['courses']
    
    def get_assigned_courses(self, obj):
        assigned_courses = obj.courses.all()
        return format_html(
            '<br>'.join([f'{course.title}' for course in assigned_courses])
        )
    get_assigned_courses.short_description = "Cursos Asignados"

admin.site.register(User, UserAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Parent)
