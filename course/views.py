from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django_filters.views import FilterView

from accounts.decorators import lecturer_required, student_required
from accounts.models import Student
from core.models import Semester
from course.filters import CourseAllocationFilter, ProgramFilter
from course.forms import (
    CourseAddForm,
    CourseAllocationForm,
    EditCourseAllocationForm,
    ProgramForm,
    UploadFormFile, 
    UploadFormVideo,
)
from course.models import (
    Course,
    CourseAllocation,
    Program,
    Upload,
    UploadVideo,
)
from result.models import TakenCourse

from django.http import HttpResponse
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch 
from reportlab.pdfgen import canvas
from django.utils import timezone
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Spacer
from datetime import datetime
from babel.dates import format_date
# ########################################################
# Program Views
# ########################################################


@method_decorator([login_required, lecturer_required], name="dispatch")
class ProgramFilterView(FilterView):
    filterset_class = ProgramFilter
    template_name = "course/program_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Programas"
        return context

def wrap_text(text, max_length):
    """ Función para envolver el texto de manera que no se corten palabras """
    words = text.split(' ')
    lines = []
    current_line = []

    for word in words:
        # Si el largo de la línea actual + la nueva palabra excede el límite, crear una nueva línea
        if sum(len(w) for w in current_line) + len(word) + len(current_line) > max_length:
            lines.append(' '.join(current_line))
            current_line = [word]
        else:
            current_line.append(word)

    if current_line:
        lines.append(' '.join(current_line))

    return lines
@login_required
@lecturer_required
def program_add(request):
    if request.method == "POST":
        form = ProgramForm(request.POST)
        if form.is_valid():
            program = form.save()
            messages.success(request, f"{program.title} program has been created.")
            return redirect("programs")
        messages.error(request, "Correct the error(s) below.")
    else:
        form = ProgramForm()
    return render(
        request, "course/program_add.html", {"title": "Add Program", "form": form}
    )


@login_required
def program_detail(request, pk):
    program = get_object_or_404(Program, pk=pk)
    courses = Course.objects.filter(program_id=pk).order_by("-year")
    credits = courses.aggregate(total_credits=Sum("credit"))
    paginator = Paginator(courses, 10)
    page = request.GET.get("page")
    courses = paginator.get_page(page)
    return render(
        request,
        "course/program_single.html",
        {
            "title": program.title,
            "program": program,
            "courses": courses,
            "credits": credits,
        },
    )


@login_required
@lecturer_required
def program_edit(request, pk):
    program = get_object_or_404(Program, pk=pk)
    if request.method == "POST":
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            program = form.save()
            messages.success(request, f"{program.title} program has been updated.")
            return redirect("programs")
        messages.error(request, "Correct the error(s) below.")
    else:
        form = ProgramForm(instance=program)
    return render(
        request, "course/program_add.html", {"title": "Edit Program", "form": form}
    )


@login_required
@lecturer_required
def program_delete(request, pk):
    program = get_object_or_404(Program, pk=pk)
    title = program.title
    program.delete()
    messages.success(request, f"Program {title} has been deleted.")
    return redirect("programs")


# ########################################################
# Course Views
# ########################################################


@login_required
def course_single(request, slug):
    course = get_object_or_404(Course, slug=slug)
    files = Upload.objects.filter(course__slug=slug)
    videos = UploadVideo.objects.filter(course__slug=slug)
    lecturers = CourseAllocation.objects.filter(courses__pk=course.id)
    return render(
        request,
        "course/course_single.html",
        {
            "title": course.title,
            "course": course,
            "files": files,
            "videos": videos,
            "lecturers": lecturers,
            "media_url": settings.MEDIA_URL,
        },
    )



@login_required
def course_video_navigation(request, slug, video_id=None):
    course = get_object_or_404(Course, slug=slug)
    videos = UploadVideo.objects.filter(course=course).order_by("timestamp")
    documents = Upload.objects.filter(course=course).order_by("upload_time")

    # Encuentra el video actual o selecciona el primero si no hay un video_id
    if video_id:
        current_video = get_object_or_404(videos, id=video_id)
    else:
        current_video = videos.first()

    # Obtener el índice del video actual y los videos anterior y siguiente
    current_index = list(videos).index(current_video)
    previous_video = videos[current_index - 1] if current_index > 0 else None
    next_video = videos[current_index + 1] if current_index < len(videos) - 1 else None

    # Verificar si es el último video
    is_last_video = current_index == len(videos) - 1

    # Obtener el documento correspondiente al video actual, si existe
    current_document = documents[current_index] if current_index < len(documents) else None

    return render(
        request,
        "course/video_navigation.html",
        {
            "course": course,
            "current_video": current_video,
            "previous_video": previous_video,
            "next_video": next_video,
            "is_last_video": is_last_video,
            "current_document": current_document,  # Documento relacionado con el video
        },
    )


@login_required
@lecturer_required
def course_add(request, pk):
    program = get_object_or_404(Program, pk=pk)
    if request.method == "POST":
        form = CourseAddForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(
                request, f"{course.title} ({course.code}) has been created."
            )
            return redirect("program_detail", pk=program.pk)
        messages.error(request, "Correct the error(s) below.")
    else:
        form = CourseAddForm(initial={"program": program})
    return render(
        request,
        "course/course_add.html",
        {"title": "Add Course", "form": form, "program": program},
    )


@login_required
@lecturer_required
def course_edit(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == "POST":
        form = CourseAddForm(request.POST, instance=course)
        if form.is_valid():
            course = form.save()
            messages.success(
                request, f"{course.title} ({course.code}) has been updated."
            )
            return redirect("program_detail", pk=course.program.pk)
        messages.error(request, "Correct the error(s) below.")
    else:
        form = CourseAddForm(instance=course)
    return render(
        request, "course/course_add.html", {"title": "Edit Course", "form": form}
    )


@login_required
@lecturer_required
def course_delete(request, slug):
    course = get_object_or_404(Course, slug=slug)
    title = course.title
    program_id = course.program.id
    course.delete()
    messages.success(request, f"Course {title} has been deleted.")
    return redirect("program_detail", pk=program_id)


# ########################################################
# Course Allocation Views
# ########################################################


@method_decorator([login_required, lecturer_required], name="dispatch")
class CourseAllocationFormView(CreateView):
    form_class = CourseAllocationForm
    template_name = "course/course_allocation_form.html"

    def form_valid(self, form):
        lecturer = form.cleaned_data["lecturer"]
        selected_courses = form.cleaned_data["courses"]
        allocation, created = CourseAllocation.objects.get_or_create(lecturer=lecturer)
        allocation.courses.set(selected_courses)
        messages.success(
            self.request, f"Courses allocated to {lecturer.get_full_name} successfully."
        )
        return redirect("course_allocation_view")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Assign Course"
        return context


@method_decorator([login_required, lecturer_required], name="dispatch")
class CourseAllocationFilterView(FilterView):
    filterset_class = CourseAllocationFilter
    template_name = "course/course_allocation_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Course Allocations"
        return context


@login_required
@lecturer_required
def edit_allocated_course(request, pk):
    allocation = get_object_or_404(CourseAllocation, pk=pk)
    if request.method == "POST":
        form = EditCourseAllocationForm(request.POST, instance=allocation)
        if form.is_valid():
            form.save()
            messages.success(request, "Course allocation has been updated.")
            return redirect("course_allocation_view")
        messages.error(request, "Correct the error(s) below.")
    else:
        form = EditCourseAllocationForm(instance=allocation)
    return render(
        request,
        "course/course_allocation_form.html",
        {"title": "Edit Course Allocation", "form": form},
    )


@login_required
@lecturer_required
def deallocate_course(request, pk):
    allocation = get_object_or_404(CourseAllocation, pk=pk)
    allocation.delete()
    messages.success(request, "Successfully deallocated courses.")
    return redirect("course_allocation_view")


# ########################################################
# File Upload Views
# ########################################################


@login_required
@lecturer_required
def handle_file_upload(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == "POST":
        form = UploadFormFile(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save(commit=False)
            upload.course = course
            upload.save()
            messages.success(request, f"{upload.title} has been uploaded.")
            return redirect("course_detail", slug=slug)
        messages.error(request, "Correct the error(s) below.")
    else:
        form = UploadFormFile()
    return render(
        request,
        "upload/upload_file_form.html",
        {"title": "File Upload", "form": form, "course": course},
    )


@login_required
@lecturer_required
def handle_file_edit(request, slug, file_id):
    course = get_object_or_404(Course, slug=slug)
    upload = get_object_or_404(Upload, pk=file_id)
    if request.method == "POST":
        form = UploadFormFile(request.POST, request.FILES, instance=upload)
        if form.is_valid():
            upload = form.save()
            messages.success(request, f"{upload.title} has been updated.")
            return redirect("course_detail", slug=slug)
        messages.error(request, "Correct the error(s) below.")
    else:
        form = UploadFormFile(instance=upload)
    return render(
        request,
        "upload/upload_file_form.html",
        {"title": "Edit File", "form": form, "course": course},
    )


@login_required
@lecturer_required
def handle_file_delete(request, slug, file_id):
    upload = get_object_or_404(Upload, pk=file_id)
    title = upload.title
    upload.delete()
    messages.success(request, f"{title} has been deleted.")
    return redirect("course_detail", slug=slug)


# ########################################################
# Video Upload Views
# ########################################################


@login_required
@lecturer_required
def handle_video_upload(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == "POST":
        form = UploadFormVideo(request.POST)
        if form.is_valid():
            video = form.save(commit=False)
            video.course = course
            video.save()
            messages.success(request, f"{video.title} ha sido agregado.")
            return redirect("course_detail", slug=slug)
        else:
            messages.error(request, "Corrige los errores a continuación.")
    else:
        form = UploadFormVideo()
    return render(
        request,
        "upload/upload_video_form.html",
        {"title": "Agregar Video", "form": form, "course": course},
    )


@login_required
def handle_video_single(request, slug, video_slug):
    course = get_object_or_404(Course, slug=slug)
    video = get_object_or_404(UploadVideo, slug=video_slug)
    return render(
        request,
        "upload/video_single.html",
        {"video": video, "course": course},
    )


@login_required
@lecturer_required
def handle_video_edit(request, slug, video_slug):
    course = get_object_or_404(Course, slug=slug)
    video = get_object_or_404(UploadVideo, slug=video_slug)
    if request.method == "POST":
        form = UploadFormVideo(request.POST, instance=video)
        if form.is_valid():
            video = form.save()
            messages.success(request, f"{video.title} ha sido actualizado.")
            return redirect("course_detail", slug=slug)
        else:
            messages.error(request, "Corrige los errores a continuación.")
    else:
        form = UploadFormVideo(instance=video)
    return render(
        request,
        "upload/upload_video_form.html",
        {"title": "Editar Video", "form": form, "course": course},
    )

@login_required
@lecturer_required
def handle_video_delete(request, slug, video_slug):
    video = get_object_or_404(UploadVideo, slug=video_slug)
    title = video.title
    video.delete()
    messages.success(request, f"{title} has been deleted.")
    return redirect("course_detail", slug=slug)


# ########################################################
# Course Registration Views
# ########################################################


@login_required
@student_required
def course_registration(request):
    if request.method == "POST":
        student = Student.objects.get(student__pk=request.user.id)
        ids = ()
        data = request.POST.copy()
        data.pop("csrfmiddlewaretoken", None)  # remove csrf_token
        for key in data.keys():
            ids = ids + (str(key),)
        for s in range(0, len(ids)):
            course = Course.objects.get(pk=ids[s])
            obj = TakenCourse.objects.create(student=student, course=course)
            obj.save()
        messages.success(request, "Courses registered successfully!")
        return redirect("course_registration")
    else:
        current_semester = Semester.objects.filter(is_current_semester=True).first()
        if not current_semester:
            messages.error(request, "No active semester found.")
            return render(request, "course/course_registration.html")

        # student = Student.objects.get(student__pk=request.user.id)
        student = get_object_or_404(Student, student__id=request.user.id)
        taken_courses = TakenCourse.objects.filter(student__student__id=request.user.id)
        t = ()
        for i in taken_courses:
            t += (i.course.pk,)

        courses = (
            Course.objects.filter(
                program__pk=student.program.id,
                level=student.level,
                semester=current_semester,
            )
            .exclude(id__in=t)
            .order_by("year")
        )
        all_courses = Course.objects.filter(
            level=student.level, program__pk=student.program.id
        )

        no_course_is_registered = False  # Check if no course is registered
        all_courses_are_registered = False

        registered_courses = Course.objects.filter(level=student.level).filter(id__in=t)
        if (
            registered_courses.count() == 0
        ):  # Check if number of registered courses is 0
            no_course_is_registered = True

        if registered_courses.count() == all_courses.count():
            all_courses_are_registered = True

        total_first_semester_credit = 0
        total_sec_semester_credit = 0
        total_registered_credit = 0
        for i in courses:
            if i.semester == "First":
                total_first_semester_credit += int(i.credit)
            if i.semester == "Second":
                total_sec_semester_credit += int(i.credit)
        for i in registered_courses:
            total_registered_credit += int(i.credit)
        context = {
            "is_calender_on": True,
            "all_courses_are_registered": all_courses_are_registered,
            "no_course_is_registered": no_course_is_registered,
            "current_semester": current_semester,
            "courses": courses,
            "total_first_semester_credit": total_first_semester_credit,
            "total_sec_semester_credit": total_sec_semester_credit,
            "registered_courses": registered_courses,
            "total_registered_credit": total_registered_credit,
            "student": student,
        }
        return render(request, "course/course_registration.html", context)


@login_required
@student_required
def course_drop(request):
    if request.method == "POST":
        student = get_object_or_404(Student, student__pk=request.user.id)
        course_ids = request.POST.getlist("course_ids")
        print("course_ids", course_ids)
        for course_id in course_ids:
            course = get_object_or_404(Course, pk=course_id)
            TakenCourse.objects.filter(student=student, course=course).delete()
        messages.success(request, "Courses dropped successfully!")
        return redirect("course_registration")

@login_required
@student_required
def download_courses_pdf(request):
    # Obtener los cursos que el estudiante tiene registrados
    student = get_object_or_404(Student, student__pk=request.user.id)
    taken_courses = TakenCourse.objects.filter(student=student)
    # Crear una respuesta HTTP con tipo de contenido PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="cursos_registrados.pdf"'

    # Crear un documento PDF
    doc = SimpleDocTemplate(response, pagesize=landscape(letter))  # Cambiar a landscape
    
    # Encabezados de la tabla
    headers = ["Nombre del Curso", "Código", "Estatus de registro", "Fecha de Inscripción", "Fecha de Vencimiento"]  # Agregar encabezados
    
    # Datos de los cursos
    data = []
    
    # Fechas fijas
    fixed_enrollment_date = "12/01/2025"
    fixed_expiration_date = "12/02/2026"
    
    # Agregar los detalles de cada curso
    for taken_course in taken_courses:
        course_name = taken_course.course.title
        course_code = taken_course.course.code
        course_status = "Inscrito" if taken_course.course.is_active else "En curso"
        data.append([course_name, course_code, course_status, fixed_enrollment_date, fixed_expiration_date])  # Usar fechas fijas

    # Crear la tabla con los datos
    table = Table([headers] + data)
    
    # Estilo de la tabla
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#BA6022')),  # Fondo gris para el encabezado
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Texto blanco en el encabezado
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),  # Alineación centrada por defecto
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Alinear "Nombre del Curso" a la izquierda
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),  # Fuente
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # Tamaño de la fuente
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Espacio debajo del encabezado
        ('TOPPADDING', (0, 1), (-1, -1), 10),  # Espacio encima de las filas de datos
        ('LINEBEFORE', (0, 0), (0, -1), 0.25, colors.black),  # Borde izquierdo
        ('LINEAFTER', (-1, 0), (-1, -1), 0.25, colors.black),  # Borde derecho
        ('LINEABOVE', (0, 0), (-1, 0), 0.25, colors.black),  # Línea encima del encabezado
        ('LINEBELOW', (0, -1), (-1, -1), 0.25, colors.black),  # Línea debajo de la última fila
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  # Rejilla para las celdas
    ]))
    
    # Crear lista de elementos para agregar al documento
    elements = []
    
    # Añadir el título "REPORTE DE PROGRESO" al documento
    title = "REPORTE DE PROGRESO"
    title_style = TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),  # Alinear el título al centro
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 16),
        ('BOTTOMPADDING', (0, 0), (0, 0), 10),
    ])
    
    # Para el título se crea una tabla con un solo elemento para tener control sobre la alineación
    title_table = Table([[title]], style=title_style, colWidths=[6 * inch])
    elements.append(title_table)

    # # Añadir un espacio entre la fecha y la tabla de cursos
    elements.append(Table([[""]], colWidths=[6 * inch], rowHeights=[0.5 * inch]))  # Espacio vacío

    # Añadir el nombre del estudiante debajo del título
    student_name = f"{student.student.first_name} {student.student.last_name}"
    name_style = TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),  # Alinear a la izquierda
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica'),
        ('FONTSIZE', (0, 0), (0, 0), 12),
        ('BOTTOMPADDING', (0, 0), (0, 0), 6),
    ])
    
    # Crear una tabla con el nombre del estudiante
    name_table = Table([[f"Nombre: {student_name}"]], style=name_style, colWidths=[6 * inch])
    elements.append(name_table)

    # Obtener la fecha actual
    current_date = format_date(datetime.now(), format='d \'de\' MMMM \'de\' y', locale='es_ES')  # Formato: 27 de Noviembre de 2024

    # Crear una tabla con la fecha
    date_style = TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),  # Alinear a la izquierda
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica'),
        ('FONTSIZE', (0, 0), (0, 0), 12),
        ('BOTTOMPADDING', (0, 0), (0, 0), 6),
    ])

    # Crear una tabla con la fecha
    date_table = Table([[f"Fecha: {current_date}"]], style=date_style, colWidths=[6 * inch])
    elements.append(date_table)

    # Añadir un espacio entre la fecha y la tabla de cursos
    elements.append(Table([[""]], colWidths=[6 * inch], rowHeights=[0.5 * inch]))  # Espacio vacío

    # Añadir la tabla de cursos al documento
    elements.append(table)

    # Construir el documento PDF
    doc.build(elements)

    return response
# ########################################################
# User Course List View
# ########################################################


@login_required
def user_course_list(request):
    if request.user.is_lecturer:
        courses = Course.objects.filter(allocated_course__lecturer__pk=request.user.id)
        return render(request, "course/user_course_list.html", {"courses": courses})

    if request.user.is_student:
        student = get_object_or_404(Student, student__pk=request.user.id)
        taken_courses = TakenCourse.objects.filter(student=student)
        return render(
            request,
            "course/user_course_list.html",
            {"student": student, "taken_courses": taken_courses},
        )

    # For other users
    return render(request, "course/user_course_list.html")
