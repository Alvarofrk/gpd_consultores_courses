from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template, render_to_string
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, FormView
from django_filters.views import FilterView
from xhtml2pdf import pisa
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
from io import BytesIO
import os
from reportlab.lib.units import inch
from reportlab.platypus import Image
from django.conf import settings
from django.urls import reverse_lazy

from accounts.decorators import admin_required
from accounts.filters import LecturerFilter, StudentFilter
from accounts.forms import (
    ParentAddForm,
    PoliciesAcceptanceForm,
    ProfileUpdateForm,
    ProgramUpdateForm,
    StaffAddForm,
    StudentAddForm,
)
from accounts.models import Parent, Student, User
from core.models import Semester, Session
from course.models import Course
from result.models import TakenCourse, Result
from accounts.utils import generate_password, send_new_account_email

# ########################################################
# Utility Functions
# ########################################################


def render_to_pdf(template_name, context):
    """Render a given template to PDF format."""
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'filename="profile.pdf"'
    template = render_to_string(template_name, context)
    pdf = pisa.CreatePDF(template, dest=response)
    if pdf.err:
        return HttpResponse("We had some problems generating the PDF")
    return response


# ########################################################
# Authentication and Registration
# ########################################################


def validate_username(request):
    username = request.GET.get("username", None)
    data = {"is_taken": User.objects.filter(username__iexact=username).exists()}
    return JsonResponse(data)


def register(request):
    if request.method == "POST":
        form = StudentAddForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully.")
            return redirect("login")
        messages.error(
            request, "Something is not correct, please fill all fields correctly."
        )
    else:
        form = StudentAddForm()
    return render(request, "registration/register.html", {"form": form})


class TermsAcceptanceView(LoginRequiredMixin, FormView):
    template_name = "accounts/terms_acceptance.html"
    form_class = PoliciesAcceptanceForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_accepted_terms and request.user.has_accepted_privacy:
            return redirect(self.get_redirect_target())
        return super().dispatch(request, *args, **kwargs)

    def get_redirect_target(self):
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        if next_url:
            return next_url
        return getattr(settings, "LOGIN_REDIRECT_URL", None) or reverse_lazy("programs")

    def get_success_url(self):
        return self.get_redirect_target()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["next_url"] = (
            self.request.POST.get("next") or self.request.GET.get("next") or ""
        )
        return context

    def form_valid(self, form):
        user = self.request.user
        user.mark_policies_accepted()
        messages.success(self.request, "Gracias por aceptar los términos de uso.")
        return redirect(self.get_success_url())


# ########################################################
# Profile Views
# ########################################################


@login_required
def profile(request):
    """Show profile of the current user."""
    current_session = Session.objects.filter(is_current_session=True).first()
    current_semester = Semester.objects.filter(
        is_current_semester=True, session=current_session
    ).first()

    context = {
        "title": request.user.get_full_name,
        "current_session": current_session,
        "current_semester": current_semester,
    }

    if request.user.is_lecturer:
        courses = Course.objects.filter(
            allocated_course__lecturer__pk=request.user.id, semester=current_semester
        )
        context["courses"] = courses
        return render(request, "accounts/profile.html", context)

    if request.user.is_student:
        student = get_object_or_404(Student, student__pk=request.user.id)
        parent = Parent.objects.filter(student=student).first()
        # Solo mostrar los cursos asignados al estudiante
        courses = student.courses.all()
        context.update(
            {
                "parent": parent,
                "courses": courses,
                "student": student,
            }
        )
        return render(request, "accounts/profile.html", context)

    # For superuser or other staff
    staff = User.objects.filter(is_lecturer=True)
    context["staff"] = staff
    return render(request, "accounts/profile.html", context)


@login_required
@admin_required
def profile_single(request, user_id):
    """Show profile of any selected user."""
    if request.user.id == user_id:
        return redirect("profile")

    current_session = Session.objects.filter(is_current_session=True).first()
    current_semester = Semester.objects.filter(
        is_current_semester=True, session=current_session
    ).first()
    user = get_object_or_404(User, pk=user_id)

    context = {
        "title": user.get_full_name,
        "user": user,
        "current_session": current_session,
        "current_semester": current_semester,
    }

    if user.is_lecturer:
        courses = Course.objects.filter(
            allocated_course__lecturer__pk=user_id, semester=current_semester
        )
        context.update(
            {
                "user_type": "Lecturer",
                "courses": courses,
            }
        )
    elif user.is_student:
        student = get_object_or_404(Student, student__pk=user_id)
        courses = TakenCourse.objects.filter(
            student__student__id=user_id, course__level=student.level
        )
        context.update(
            {
                "user_type": "Student",
                "courses": courses,
                "student": student,
            }
        )
    else:
        context["user_type"] = "Superuser"

    if request.GET.get("download_pdf"):
        return render_to_pdf("pdf/profile_single.html", context)

    return render(request, "accounts/profile_single.html", context)


@login_required
@admin_required
def admin_panel(request):
    return render(request, "setting/admin_panel.html", {"title": "Admin Panel"})


# ########################################################
# Settings Views
# ########################################################


@login_required
def profile_update(request):
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect("profile")
        messages.error(request, "Please correct the error(s) below.")
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, "setting/profile_info_change.html", {"form": form})


@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect("profile")
        messages.error(request, "Please correct the error(s) below.")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "setting/password_change.html", {"form": form})


# ########################################################
# Staff (Lecturer) Views
# ########################################################


@login_required
@admin_required
def staff_add_view(request):
    if request.method == "POST":
        form = StaffAddForm(request.POST)
        if form.is_valid():
            lecturer = form.save()
            username = form.cleaned_data.get('username')
            password = generate_password(username)
            lecturer.set_password(password)
            lecturer.save()
            full_name = lecturer.get_full_name
            email = lecturer.email
            messages.success(
                request,
                f"Account for lecturer {full_name} has been created. "
                f"An email with account credentials will be sent to {email} within a minute.",
            )
            send_new_account_email(lecturer, password)
            return redirect("lecturer_list")
    else:
        form = StaffAddForm()
    return render(
        request, "accounts/add_staff.html", {"title": "Add Lecturer", "form": form}
    )


@login_required
@admin_required
def edit_staff(request, pk):
    lecturer = get_object_or_404(User, is_lecturer=True, pk=pk)
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=lecturer)
        if form.is_valid():
            form.save()
            full_name = lecturer.get_full_name
            messages.success(request, f"Lecturer {full_name} has been updated.")
            return redirect("lecturer_list")
        messages.error(request, "Please correct the error below.")
    else:
        form = ProfileUpdateForm(instance=lecturer)
    return render(
        request, "accounts/edit_lecturer.html", {"title": "Edit Lecturer", "form": form}
    )


@method_decorator([login_required, admin_required], name="dispatch")
class LecturerFilterView(FilterView):
    filterset_class = LecturerFilter
    queryset = User.objects.filter(is_lecturer=True)
    template_name = "accounts/lecturer_list.html"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lecturers"
        return context


@login_required
@admin_required
def lecturer_list_pdf(request):
    lecturers = User.objects.filter(is_lecturer=True).order_by('first_name', 'last_name')
    
    # Crear el PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="lista_instructores_gpd.pdf"'
    
    # Crear el documento PDF en landscape para mejor aprovechamiento del espacio
    doc = SimpleDocTemplate(response, pagesize=landscape(letter), 
                           topMargin=0.3*inch,  # Margen superior reducido
                           bottomMargin=0.5*inch,
                           leftMargin=0.5*inch,
                           rightMargin=0.5*inch)
    elements = []
    
    # Estilos modernos
    styles = getSampleStyleSheet()
    
    # Estilo para el título principal
    title_style = ParagraphStyle(
        'ModernTitle',
        parent=styles['Heading1'],
        fontSize=28,
        spaceAfter=30,
        textColor=colors.HexColor('#033b80'),  # Azul GPD
        alignment=1,  # Centrado
        fontName='Helvetica-Bold',
        leading=32
    )
    
    # Estilo para información del sistema
    info_style = ParagraphStyle(
        'SystemInfo',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=15,
        textColor=colors.HexColor('#6c757d'),
        alignment=2,  # Derecha
        fontName='Helvetica'
    )
    
    # Estilo para el pie de página
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#6c757d'),
        alignment=1,
        fontName='Helvetica'
    )
    
    # ENCABEZADO: Agregar logos arriba de todo
    try:
        logo1_path = settings.STATICFILES_DIRS[0] + "/img/logo1.jpg"
        logoaniversario_path = settings.STATICFILES_DIRS[0] + "/img/logoaniversario.png"
        
        # Crear tabla para los logos (2 columnas)
        logo_data = []
        logo_row = []
        
        # Logo 1 (tamaño normal)
        if os.path.exists(logo1_path):
            logo1 = Image(logo1_path, width=2*inch, height=1.5*inch)
            logo_row.append(logo1)
        else:
            logo_row.append("")
        
        # Logo aniversario (más pequeño)
        if os.path.exists(logoaniversario_path):
            logoaniversario = Image(logoaniversario_path, width=1.5*inch, height=1.125*inch)  # 25% más pequeño
            logo_row.append(logoaniversario)
        else:
            logo_row.append("")
        
        logo_data.append(logo_row)
        
        # Crear tabla con los logos
        logo_table = Table(logo_data, colWidths=[3*inch, 3*inch])
        logo_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        elements.append(logo_table)
        elements.append(Spacer(1, 20))
    except:
        pass  # Si no encuentra los logos, continúa sin ellos
    
    # Título principal
    elements.append(Paragraph("LISTA DE INSTRUCTORES", title_style))
    
    # Información de generación
    current_date = datetime.now().strftime('%d/%m/%Y')
    current_time = datetime.now().strftime('%H:%M')
    elements.append(Paragraph(f"Generado el: {current_date} a las {current_time}", info_style))
    
    # Estadísticas
    total_lecturers = lecturers.count()
    elements.append(Paragraph(f"Total de instructores: {total_lecturers}", info_style))
    elements.append(Spacer(1, 20))
    
    # Tabla de instructores con diseño moderno
    headers = ['#', 'ID', 'Nombres y Apellidos', 'Correo Electrónico', 'Teléfono', 'Dirección']
    
    data = [headers]  # Primera fila son los headers
    
    # Agregar datos de instructores
    for i, lecturer in enumerate(lecturers, 1):
        data.append([
            str(i),
            str(lecturer.id),
            lecturer.get_full_name,
            lecturer.email or '-',
            lecturer.phone or '-',
            lecturer.address or '-'
        ])
    
    # Crear tabla con anchos de columna optimizados
    col_widths = [30, 50, 200, 150, 100, 200]  # Anchos en puntos
    table = Table(data, colWidths=col_widths)
    
    # Estilo moderno para la tabla con letras más pequeñas
    table_style = TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#033b80')),  # Azul GPD
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),  # Reducido de 11 a 9
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),  # Reducido de 12 a 10
        ('TOPPADDING', (0, 0), (-1, 0), 10),  # Reducido de 12 a 10
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#042042')),
        
        # Data rows styling con letras más pequeñas
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),  # Reducido de 9 a 7
        ('TOPPADDING', (0, 1), (-1, -1), 6),  # Reducido de 8 a 6
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),  # Reducido de 8 a 6
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Número centrado
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # ID centrado
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),    # Nombre a la izquierda
        ('ALIGN', (3, 1), (3, -1), 'LEFT'),    # Email a la izquierda
        ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Teléfono centrado
        ('ALIGN', (5, 1), (5, -1), 'LEFT'),    # Dirección a la izquierda
        
        # Grid styling
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e9ecef')),
        ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#033b80')),
        
        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
    ])
    
    table.setStyle(table_style)
    elements.append(table)
    
    # Espacio final (sin pie de página)
    elements.append(Spacer(1, 30))
    
    # Construir el PDF
    doc.build(elements)
    
    return response


@login_required
@admin_required
def delete_staff(request, pk):
    lecturer = get_object_or_404(User, is_lecturer=True, pk=pk)
    full_name = lecturer.get_full_name
    lecturer.delete()
    messages.success(request, f"Lecturer {full_name} has been deleted.")
    return redirect("lecturer_list")


# ########################################################
# Student Views
# ########################################################


@login_required
@admin_required
def student_add_view(request):
    if request.method == "POST":
        form = StudentAddForm(request.POST)
        if form.is_valid():
            student = form.save()
            full_name = student.get_full_name
            email = student.email
            
            # Obtener información sobre los cursos asignados
            student_obj = Student.objects.get(student=student)
            courses_count = student_obj.courses.count()
            
            if courses_count > 0:
                courses_list = ", ".join([course.title for course in student_obj.courses.all()[:3]])
                if courses_count > 3:
                    courses_list += f" y {courses_count - 3} más"
                
                messages.success(
                    request,
                    f"Participante {full_name} creado exitosamente. "
                    f"Inscrito en {courses_count} curso(s): {courses_list}. "
                    f"Las credenciales se enviarán a {email}."
                )
            else:
                messages.success(
                    request,
                    f"Participante {full_name} creado exitosamente. "
                    f"Puedes asignarle cursos desde la lista de participantes. "
                    f"Las credenciales se enviarán a {email}."
                )
            
            return redirect("student_list")
        messages.error(request, "Por favor corrige los errores indicados abajo.")
    else:
        form = StudentAddForm()
    
    return render(
        request, 
        "accounts/add_student.html", 
        {
            "title": "Crear Participante", 
            "form": form
        }
    )


@login_required
@admin_required
def edit_student(request, pk):
    student_user = get_object_or_404(User, is_student=True, pk=pk)
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=student_user)
        if form.is_valid():
            form.save()
            full_name = student_user.get_full_name
            messages.success(request, f"Student {full_name} has been updated.")
            return redirect("student_list")
        messages.error(request, "Please correct the error below.")
    else:
        form = ProfileUpdateForm(instance=student_user)
    return render(
        request, "accounts/edit_student.html", {"title": "Edit Student", "form": form}
    )


@method_decorator([login_required, admin_required], name="dispatch")
class StudentListView(FilterView):
    queryset = Student.objects.all()
    filterset_class = StudentFilter
    template_name = "accounts/student_list.html"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Students"
        return context


@login_required
@admin_required
def render_student_pdf_list(request):
    students = Student.objects.all().order_by('student__first_name', 'student__last_name')
    
    # Crear el PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="lista_participantes_gpd.pdf"'
    
    # Crear el documento PDF en landscape para mejor aprovechamiento del espacio
    doc = SimpleDocTemplate(response, pagesize=landscape(letter), 
                           topMargin=0.3*inch,  # Margen superior reducido
                           bottomMargin=0.5*inch,
                           leftMargin=0.5*inch,
                           rightMargin=0.5*inch)
    elements = []
    
    # Estilos modernos
    styles = getSampleStyleSheet()
    
    # Estilo para el título principal
    title_style = ParagraphStyle(
        'ModernTitle',
        parent=styles['Heading1'],
        fontSize=28,
        spaceAfter=30,
        textColor=colors.HexColor('#033b80'),  # Azul GPD
        alignment=1,  # Centrado
        fontName='Helvetica-Bold',
        leading=32
    )
    
    # Estilo para información del sistema
    info_style = ParagraphStyle(
        'SystemInfo',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=15,
        textColor=colors.HexColor('#6c757d'),
        alignment=2,  # Derecha
        fontName='Helvetica'
    )
    
    # Estilo para el pie de página
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#6c757d'),
        alignment=1,
        fontName='Helvetica'
    )
    
    # ENCABEZADO: Agregar logos arriba de todo
    try:
        logo1_path = settings.STATICFILES_DIRS[0] + "/img/logo1.jpg"
        logoaniversario_path = settings.STATICFILES_DIRS[0] + "/img/logoaniversario.png"
        
        # Crear tabla para los logos (2 columnas)
        logo_data = []
        logo_row = []
        
        # Logo 1 (tamaño normal)
        if os.path.exists(logo1_path):
            logo1 = Image(logo1_path, width=2*inch, height=1.5*inch)
            logo_row.append(logo1)
        else:
            logo_row.append("")
        
        # Logo aniversario (más pequeño)
        if os.path.exists(logoaniversario_path):
            logoaniversario = Image(logoaniversario_path, width=1.5*inch, height=1.125*inch)  # 25% más pequeño
            logo_row.append(logoaniversario)
        else:
            logo_row.append("")
        
        logo_data.append(logo_row)
        
        # Crear tabla con los logos
        logo_table = Table(logo_data, colWidths=[3*inch, 3*inch])
        logo_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        elements.append(logo_table)
        elements.append(Spacer(1, 20))
    except:
        pass  # Si no encuentra los logos, continúa sin ellos
    
    # Título principal
    elements.append(Paragraph("LISTA DE PARTICIPANTES", title_style))
    
    # Información de generación
    current_date = datetime.now().strftime('%d/%m/%Y')
    current_time = datetime.now().strftime('%H:%M')
    elements.append(Paragraph(f"Generado el: {current_date} a las {current_time}", info_style))
    
    # Estadísticas
    total_students = students.count()
    elements.append(Paragraph(f"Total de participantes: {total_students}", info_style))
    elements.append(Spacer(1, 20))
    
    # Tabla de participantes con diseño moderno
    headers = ['#', 'DNI', 'Nombres y Apellidos', 'Correo Electrónico', 'Teléfono', 'Empresa', 'Cargo', 'Programa']
    
    data = [headers]  # Primera fila son los headers
    
    # Agregar datos de participantes
    for i, student in enumerate(students, 1):
        data.append([
            str(i),
            student.student.username,
            student.student.get_full_name,
            student.student.email or '-',
            student.student.phone or '-',
            student.empresa or '-',
            student.cargo or '-',
            str(student.program) if student.program else '-'
        ])
    
    # Crear tabla con anchos de columna optimizados
    col_widths = [30, 80, 150, 120, 80, 100, 100, 100]  # Anchos en puntos
    table = Table(data, colWidths=col_widths)
    
    # Estilo moderno para la tabla con letras más pequeñas
    table_style = TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#033b80')),  # Azul GPD
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),  # Reducido de 11 a 9
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),  # Reducido de 12 a 10
        ('TOPPADDING', (0, 0), (-1, 0), 10),  # Reducido de 12 a 10
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#042042')),
        
        # Data rows styling con letras más pequeñas
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),  # Reducido de 9 a 7
        ('TOPPADDING', (0, 1), (-1, -1), 6),  # Reducido de 8 a 6
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),  # Reducido de 8 a 6
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Número centrado
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # DNI centrado
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),    # Nombre a la izquierda
        ('ALIGN', (3, 1), (3, -1), 'LEFT'),    # Email a la izquierda
        ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Teléfono centrado
        ('ALIGN', (5, 1), (5, -1), 'LEFT'),    # Empresa a la izquierda
        ('ALIGN', (6, 1), (6, -1), 'LEFT'),    # Cargo a la izquierda
        ('ALIGN', (7, 1), (7, -1), 'LEFT'),    # Programa a la izquierda
        
        # Grid styling
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e9ecef')),
        ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#033b80')),
        
        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
    ])
    
    table.setStyle(table_style)
    elements.append(table)
    
    # Espacio final (sin pie de página)
    elements.append(Spacer(1, 30))
    
    # Construir el PDF
    doc.build(elements)
    
    return response


@login_required
@admin_required
def delete_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    full_name = student.student.get_full_name
    student.delete()
    messages.success(request, f"Student {full_name} has been deleted.")
    return redirect("student_list")


@login_required
@admin_required
def edit_student_program(request, pk):
    student = get_object_or_404(Student, student_id=pk)
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = ProgramUpdateForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            full_name = user.get_full_name
            messages.success(request, f"{full_name}'s program has been updated.")
            return redirect("profile_single", user_id=pk)
        messages.error(request, "Please correct the error(s) below.")
    else:
        form = ProgramUpdateForm(instance=student)
    return render(
        request,
        "accounts/edit_student_program.html",
        {"title": "Edit Program", "form": form, "student": student},
    )


# ########################################################
# Parent Views
# ########################################################


@method_decorator([login_required, admin_required], name="dispatch")
class ParentAdd(CreateView):
    model = Parent
    form_class = ParentAddForm
    template_name = "accounts/parent_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Parent added successfully.")
        return super().form_valid(form)


@login_required
@admin_required
def manage_student_courses(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        try:
            # Obtener los IDs de los cursos seleccionados
            course_ids = request.POST.getlist('courses')
            
            # Obtener los cursos actuales y los nuevos seleccionados
            current_courses = set(student.courses.all())
            new_courses = set(Course.objects.filter(id__in=course_ids))
            
            # Cursos a agregar (nuevos - actuales)
            courses_to_add = new_courses - current_courses
            # Cursos a remover (actuales - nuevos)
            courses_to_remove = current_courses - new_courses
            
            # Actualizar los cursos del estudiante
            student.courses.clear()
            if course_ids:
                student.courses.add(*new_courses)
            
            # Actualizar el estado de los cursos en TakenCourse
            TakenCourse.objects.filter(
                student=student,
                course__in=courses_to_remove
            ).delete()
            
            # Agregar nuevos cursos
            for course in courses_to_add:
                TakenCourse.objects.get_or_create(
                    student=student,
                    course=course,
                    defaults={
                        'grade': None,
                        'comment': 'Curso asignado por administrador'
                    }
                )
            
            # Eliminar registros de progreso y calificaciones de cursos removidos
            Result.objects.filter(
                student=student,
                level=student.level
            ).delete()
            
            messages.success(request, 'Los cursos han sido actualizados exitosamente')
            return redirect('student_list')
        except Exception as e:
            messages.error(request, f'Error al actualizar los cursos: {str(e)}')
            return redirect('manage_student_courses', student_id=student_id)
    
    # Obtener todos los cursos disponibles
    all_courses = Course.objects.filter(is_active=True).order_by('title')
    
    # Si el estudiante tiene un programa asignado, incluir los cursos del programa
    if student.program:
        program_courses = Course.objects.filter(
            program=student.program,
            is_active=True
        ).order_by('title')
        all_courses = all_courses | program_courses
    
    # Obtener los cursos actuales del estudiante
    current_courses = student.courses.all()
    
    context = {
        'student': student,
        'all_courses': all_courses.distinct(),
        'current_courses': current_courses,
    }
    return render(request, 'accounts/manage_student_courses.html', context)
