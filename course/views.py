from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, View
from django_filters.views import FilterView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse, FileResponse, Http404
import os

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
    Program,
    Course,
    CourseAllocation,
    Upload,
    UploadVideo,
    VideoCompletion,
    DocumentCompletion,
)
from result.models import TakenCourse

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch 
from reportlab.pdfgen import canvas
from django.utils import timezone
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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
    from .optimizations import CourseOptimizations, CourseCache
    
    course = get_object_or_404(Course, slug=slug)
    
    # OPTIMIZACIÓN: Usar método optimizado para obtener videos con información de completado
    videos = CourseOptimizations.get_optimized_videos_with_completion(course, request.user)
    documents = Upload.objects.filter(course=course).order_by("upload_time")

    # Si no hay videos pero hay documentos, mostrar el primer documento
    if not videos.exists() and documents.exists():
        # Redirigir a una vista especial para cursos solo con documentos
        return redirect('course_document_navigation', slug=slug, document_id=documents.first().id)
    
    # Si no hay videos ni documentos, mostrar mensaje de error
    if not videos.exists() and not documents.exists():
        messages.error(request, "Este curso no tiene contenido disponible (videos o documentos).")
        return redirect('course_single', slug=slug)

    # Convertir QuerySet a lista para acceso por índice (necesario para la lógica existente)
    videos_list = list(videos)

    # Encuentra el video actual o selecciona el primero si no hay un video_id
    if video_id:
        current_video = get_object_or_404(UploadVideo, id=video_id, course=course)
        # Encontrar el índice del video actual en la lista optimizada
        try:
            current_index = next(i for i, v in enumerate(videos_list) if v.id == current_video.id)
        except StopIteration:
            # Si no se encuentra, usar el primer video
            current_video = videos_list[0] if videos_list else None
            current_index = 0
    else:
        current_video = videos_list[0] if videos_list else None
        current_index = 0

    # Si no hay video actual, redirigir al primer video
    if current_video is None:
        return redirect('course_single', slug=slug)

    # Obtener videos anterior y siguiente usando índices
    previous_video = videos_list[current_index - 1] if current_index > 0 else None
    next_video = videos_list[current_index + 1] if current_index < len(videos_list) - 1 else None

    # Verificar si es el último video
    is_last_video = current_index == len(videos_list) - 1

    # Obtener el documento correspondiente al video actual, si existe
    documents_list = list(documents)
    current_document = documents_list[current_index] if current_index < len(documents_list) else None

    # OPTIMIZACIÓN: is_completed ya viene calculado en la consulta optimizada
    is_completed = current_video.is_completed if hasattr(current_video, 'is_completed') else False

    # OPTIMIZACIÓN: completed_videos ya viene calculado en la consulta optimizada
    completed_videos = [video for video in videos_list if getattr(video, 'is_completed', False)]

    # Verificar si se puede avanzar al siguiente video
    can_proceed = is_completed or current_index == 0 or request.user.is_staff or request.user.is_lecturer

    # Si el usuario no es staff ni instructor, verificar si puede acceder a este video
    if not request.user.is_staff and not request.user.is_lecturer:
        # Si no es el primer video, verificar si el anterior está completado
        if current_index > 0:
            previous_video_obj = videos_list[current_index - 1]
            if not getattr(previous_video_obj, 'is_completed', False):
                return redirect('course_video_navigation', slug=slug, video_id=previous_video_obj.id)

    # Manejar la marca de completado
    if request.method == 'POST' and 'mark_completed' in request.POST:
        if not is_completed:
            VideoCompletion.objects.create(user=request.user, video=current_video)
            is_completed = True
            # Actualizar el estado en la lista para evitar consultas adicionales
            current_video.is_completed = True
            # Invalidar caché de progreso del usuario
            CourseCache.invalidate_user_progress_cache(request.user.id)
        return redirect('course_video_navigation', slug=slug, video_id=current_video.id)

    return render(
        request,
        "course/video_navigation.html",
        {
            "course": course,
            "current_video": current_video,
            "previous_video": previous_video,
            "next_video": next_video,
            "is_last_video": is_last_video,
            "current_document": current_document,
            "is_completed": is_completed,
            "can_proceed": can_proceed,
            "videos": videos_list,  # Usar la lista optimizada
            "completed_videos": completed_videos,
            "current_user": request.user,
            "current_index": current_index,
            "total_videos": len(videos_list),
        },
    )


@login_required
def course_document_navigation(request, slug, document_id=None):
    """
    Vista para navegar por documentos cuando no hay videos en el curso
    """
    from .optimizations import CourseOptimizations, CourseCache
    
    course = get_object_or_404(Course, slug=slug)
    
    # OPTIMIZACIÓN: Usar método optimizado para obtener documentos con información de completado
    documents = CourseOptimizations.get_optimized_documents_with_completion(course, request.user)
    
    # Si no hay documentos, redirigir al curso
    if not documents.exists():
        messages.error(request, "Este curso no tiene documentos disponibles.")
        return redirect('course_single', slug=slug)
    
    # Convertir QuerySet a lista para acceso por índice
    document_list = list(documents)
    
    # Encuentra el documento actual o selecciona el primero si no hay un document_id
    if document_id:
        current_document = get_object_or_404(Upload, id=document_id, course=course)
        # Encontrar el índice del documento actual en la lista optimizada
        try:
            current_index = next(i for i, d in enumerate(document_list) if d.id == current_document.id)
        except StopIteration:
            # Si no se encuentra, usar el primer documento
            current_document = document_list[0] if document_list else None
            current_index = 0
    else:
        current_document = document_list[0] if document_list else None
        current_index = 0
    
    # Obtener documentos anterior y siguiente usando índices
    previous_document = document_list[current_index - 1] if current_index > 0 else None
    next_document = document_list[current_index + 1] if current_index < len(document_list) - 1 else None
    
    # Verificar si es el último documento
    is_last_document = current_index == len(document_list) - 1
    
    # OPTIMIZACIÓN: is_completed ya viene calculado en la consulta optimizada
    is_completed = current_document.is_completed if hasattr(current_document, 'is_completed') else False
    
    # Verificar si se puede avanzar al siguiente documento
    can_proceed = is_completed or current_index == 0 or request.user.is_staff or request.user.is_lecturer
    
    # Si el usuario no es staff ni instructor, verificar si puede acceder a este documento
    if not request.user.is_staff and not request.user.is_lecturer:
        # Si no es el primer documento, verificar si el anterior está completado
        if current_index > 0:
            previous_document_obj = document_list[current_index - 1]
            if not getattr(previous_document_obj, 'is_completed', False):
                return redirect('course_document_navigation', slug=slug, document_id=previous_document_obj.id)
    
    # Manejar la marca de completado
    if request.method == 'POST' and 'mark_completed' in request.POST:
        if not is_completed:
            current_document.mark_as_completed(request.user)
            is_completed = True
            # Actualizar el estado en la lista para evitar consultas adicionales
            current_document.is_completed = True
            # Invalidar caché de progreso del usuario
            CourseCache.invalidate_user_progress_cache(request.user.id)
        return redirect('course_document_navigation', slug=slug, document_id=current_document.id)
    
    # Preparar contexto para PowerPoint
    powerpoint_data = None
    if current_document.get_extension_short() == 'powerpoint':
        if current_document.has_embedded_videos():
            # PPTX con videos - mostrar mensaje y opción de descarga
            powerpoint_data = {
                'has_videos': True,
                'slide_count': current_document.get_slide_count(),
                'message': 'Esta presentación contiene videos embebidos que no se pueden reproducir en el navegador. Te recomendamos descargar el archivo para una experiencia completa.'
            }
        else:
            # PPTX sin videos - convertir a HTML para visualización
            slides_html = current_document.convert_pptx_to_html()
            if slides_html:
                powerpoint_data = {
                    'has_videos': False,
                    'slides_html': slides_html,
                    'slide_count': len(slides_html),
                    'current_slide': 1
                }
    
    context = {
        'course': course,
        'current_document': current_document,
        'previous_document': previous_document,
        'next_document': next_document,
        'documents': documents,
        'powerpoint_data': powerpoint_data,
        'is_last_document': is_last_document,
        'is_completed': is_completed,
        'can_proceed': can_proceed,
        'current_index': current_index,
        'total_documents': len(document_list),
    }
    
    return render(request, 'course/document_navigation.html', context)


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
            
            # Limpiar campos según el tipo de subida
            upload_type = form.cleaned_data.get('upload_type')
            if upload_type == 'file':
                upload.external_url = None
            elif upload_type == 'url':
                upload.file = None
            
            upload.save()
            messages.success(request, f"{upload.title} ha sido subido correctamente.")
            return redirect("course_detail", slug=slug)
        messages.error(request, "Corrige los errores a continuación.")
    else:
        form = UploadFormFile()
    return render(
        request,
        "upload/upload_file_form.html",
        {"title": "Subir Archivo", "form": form, "course": course},
    )


@login_required
@lecturer_required
def handle_file_edit(request, slug, file_id):
    course = get_object_or_404(Course, slug=slug)
    upload = get_object_or_404(Upload, pk=file_id)
    if request.method == "POST":
        form = UploadFormFile(request.POST, request.FILES, instance=upload)
        if form.is_valid():
            upload = form.save(commit=False)
            
            # Limpiar campos según el tipo de subida
            upload_type = form.cleaned_data.get('upload_type')
            if upload_type == 'file':
                upload.external_url = None
            elif upload_type == 'url':
                upload.file = None
            
            upload.save()
            messages.success(request, f"{upload.title} ha sido actualizado correctamente.")
            return redirect("course_detail", slug=slug)
        messages.error(request, "Corrige los errores a continuación.")
    else:
        form = UploadFormFile(instance=upload)
        # Establecer el tipo de subida basado en los datos existentes
        if upload.external_url:
            form.fields['upload_type'].initial = 'url'
        else:
            form.fields['upload_type'].initial = 'file'
    return render(
        request,
        "upload/upload_file_form.html",
        {"title": "Editar Archivo", "form": form, "course": course},
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
    try:
        # Obtener los cursos que el estudiante tiene registrados
        student = get_object_or_404(Student, student__pk=request.user.id)
        taken_courses = TakenCourse.objects.filter(student=student).select_related('course').order_by('course__title')
        courses = [taken_course.course for taken_course in taken_courses]
        
        if not courses:
            messages.error(request, "No tienes cursos inscritos para generar el PDF.")
            return redirect('user_course_list')
        
        # SIMPLIFICACIÓN: Usar consultas directas más simples para evitar timeouts
        # Obtener solo los datos necesarios para el PDF
        status_data = {}
        for course in courses:
            # Calcular progreso básico sin optimizaciones complejas
            videos = UploadVideo.objects.filter(course=course)
            documents = Upload.objects.filter(course=course)
            
            total_content = videos.count() + documents.count()
            if total_content == 0:
                status_data[course.id] = 'not_started'
                continue
                
            completed_videos = VideoCompletion.objects.filter(
                user=request.user, video__in=videos
            ).count()
            completed_docs = DocumentCompletion.objects.filter(
                user=request.user, document__in=documents
            ).count()
            
            completed_content = completed_videos + completed_docs
            progress = round((completed_content / total_content) * 100, 1) if total_content > 0 else 0
            
            # Estado simplificado
            if progress >= 100:
                status_data[course.id] = 'course_completed'
            elif progress > 0:
                status_data[course.id] = 'material_in_progress'
            else:
                status_data[course.id] = 'not_started'
        
        # Crear el PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'filename="consolidado_cursos_gpd.pdf"'
        
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
        
        # ENCABEZADO SIMPLIFICADO: Solo texto para evitar problemas de imágenes
        elements.append(Paragraph("CONSOLIDADO DE CURSOS GPD", title_style))
        elements.append(Spacer(1, 20))
        
        # Título principal
        elements.append(Paragraph("CONSOLIDADO DE CURSOS", title_style))
        
        # Información del estudiante
        student_name = f"{student.student.first_name} {student.student.last_name}"
        student_info = Paragraph(f"Participante: {student_name}", info_style)
        elements.append(student_info)
        
        # Información de generación
        current_date = datetime.now().strftime('%d/%m/%Y')
        current_time = datetime.now().strftime('%H:%M')
        elements.append(Paragraph(f"Generado el: {current_date} a las {current_time}", info_style))
        
        # Estadísticas
        total_courses = len(courses)
        elements.append(Paragraph(f"Total de cursos inscritos: {total_courses}", info_style))
        elements.append(Spacer(1, 20))
        
        # Tabla de cursos con diseño moderno (sin fechas)
        headers = ['#', 'Código', 'Nombre del Curso', 'Estado']
        
        data = [headers]  # Primera fila son los headers
        
        # OPTIMIZACIÓN: Usar datos pre-calculados en lugar de consultas individuales
        for i, taken_course in enumerate(taken_courses, 1):
            course = taken_course.course
            course_id = course.id
            
            # Usar datos optimizados en lugar de get_course_status_for_user()
            course_status = status_data.get(course_id, 'not_started')
            
            # Determinar el estado para mostrar en el PDF
            if course_status == 'course_completed':
                pdf_status = "Completo"
            elif course_status == 'material_in_progress':
                pdf_status = "En Curso"
            elif course_status == 'exam_available':
                pdf_status = "En Curso"
            elif course_status == 'exam_failed':
                pdf_status = "En Curso"
            else:
                pdf_status = "Inscrito"
            
            data.append([
                str(i),
                course.code,
                course.title,
                pdf_status
            ])
        
        # Crear tabla con anchos de columna optimizados (sin columnas de fechas)
        col_widths = [40, 100, 350, 120]  # Anchos en puntos ajustados
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
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Código centrado
            ('ALIGN', (2, 1), (2, -1), 'LEFT'),    # Nombre a la izquierda
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Estado centrado
            
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
        
    except Exception as e:
        # Manejo de errores robusto
        messages.error(request, f"Error generando PDF: {str(e)}")
        return redirect('user_course_list')
# ########################################################
# User Course List View
# ########################################################


@login_required
def user_course_list(request):
    if request.user.is_lecturer:
        courses = Course.objects.filter(allocated_course__lecturer__pk=request.user.id)
        return render(request, "course/user_course_list.html", {"courses": courses})

    if request.user.is_student:
        from .optimizations import CourseOptimizations, CourseCache
        
        student = get_object_or_404(Student, student__pk=request.user.id)
        
        # Optimización: Obtener taken_courses con select_related para evitar consultas adicionales
        taken_courses = TakenCourse.objects.filter(student=student).select_related('course')
        courses = [taken_course.course for taken_course in taken_courses]
        
        # Calcular estadísticas del estudiante
        total_courses = len(courses)
        
        if total_courses == 0:
            context = {
                "student": student, 
                "taken_courses": taken_courses,
                "courses_with_progress": [],
                "total_courses": 0,
                "completed_courses": 0,
                "in_progress_courses": 0,
                "exam_available_courses": 0,
                "exam_failed_courses": 0,
                "not_started_courses": 0,
                "avg_progress": 0,
            }
            return render(request, "course/user_course_list.html", context)
        
        # OPTIMIZACIÓN CRÍTICA: Obtener todos los datos en consultas agrupadas
        # En lugar de 241 consultas, ahora solo ~15 consultas
        
        # Verificar caché primero
        cached_data = CourseCache.get_cached_bulk_progress(request.user.id)
        
        if cached_data and len(cached_data.get('course_ids', [])) == len(courses):
            # Usar datos del caché si están disponibles y actualizados
            progress_data = cached_data.get('progress_data', {})
            content_data = cached_data.get('content_data', {})
            status_data = cached_data.get('status_data', {})
            exam_data = cached_data.get('exam_data', {})
        else:
            # 1. Obtener progreso de todos los cursos en una sola consulta
            progress_data = CourseOptimizations.get_bulk_progress_for_courses(courses, request.user)
            
            # 2. Obtener resumen de contenido de todos los cursos en una sola consulta
            content_data = CourseOptimizations.get_bulk_content_summary(courses)
            
            # 3. Obtener estado de todos los cursos en consultas optimizadas
            status_data = CourseOptimizations.get_bulk_course_status(courses, request.user)
            
            # 4. Obtener información de exámenes de todos los cursos en consultas optimizadas
            exam_data = CourseOptimizations.get_bulk_exam_info(courses, request.user)
            
            # Guardar en caché
            cache_data = {
                'course_ids': [course.id for course in courses],
                'progress_data': progress_data,
                'content_data': content_data,
                'status_data': status_data,
                'exam_data': exam_data,
            }
            CourseCache.set_cached_bulk_progress(request.user.id, cache_data)
        
        # Procesar datos y construir respuesta
        completed_courses = 0
        in_progress_courses = 0
        exam_available_courses = 0
        exam_failed_courses = 0
        total_progress = 0
        
        courses_with_progress = []
        
        for taken_course in taken_courses:
            course = taken_course.course
            course_id = course.id
            
            # Obtener datos desde las consultas optimizadas
            progress_info = progress_data.get(course_id, {'progress': 0})
            material_progress = progress_info['progress']
            
            content_summary = content_data.get(course_id, {
                'total_videos': 0,
                'total_documents': 0,
                'total_content': 0,
                'has_videos': False,
                'has_documents': False,
            })
            
            # Construir completion_summary desde progress_info
            completion_summary = {
                'completed_videos': progress_info.get('completed_videos', 0),
                'completed_documents': progress_info.get('completed_documents', 0),
                'completed_content': progress_info.get('completed_content', 0),
                'total_videos': progress_info.get('total_videos', 0),
                'total_documents': progress_info.get('total_documents', 0),
                'total_content': progress_info.get('total_content', 0),
            }
            
            course_status = status_data.get(course_id, 'not_started')
            exam_info = exam_data.get(course_id)
            
            # Contar cursos por estado
            if course_status == 'course_completed':
                completed_courses += 1
            elif course_status == 'material_in_progress':
                in_progress_courses += 1
            elif course_status == 'exam_available':
                exam_available_courses += 1
            elif course_status == 'exam_failed':
                exam_failed_courses += 1
            
            total_progress += material_progress
            
            courses_with_progress.append({
                'taken_course': taken_course,
                'course': course,
                'material_progress': material_progress,
                'course_status': course_status,
                'content_summary': content_summary,
                'completion_summary': completion_summary,
                'exam_info': exam_info,
            })
        
        # Calcular estadísticas generales
        avg_progress = round(total_progress / total_courses, 1) if total_courses > 0 else 0
        
        context = {
            "student": student, 
            "taken_courses": taken_courses,
            "courses_with_progress": courses_with_progress,
            "total_courses": total_courses,
            "completed_courses": completed_courses,
            "in_progress_courses": in_progress_courses,
            "exam_available_courses": exam_available_courses,
            "exam_failed_courses": exam_failed_courses,
            "not_started_courses": total_courses - completed_courses - in_progress_courses - exam_available_courses - exam_failed_courses,
            "avg_progress": avg_progress,
        }
        
        return render(request, "course/user_course_list.html", context)

    # For other users
    return render(request, "course/user_course_list.html")

@login_required
@staff_member_required
def update_video_order(request, video_id):
    if request.method == 'POST':
        video = get_object_or_404(UploadVideo, id=video_id)
        try:
            new_order = int(request.POST.get('order', 0))
            video.order = new_order
            video.save()
            messages.success(request, _('Orden del video actualizado correctamente.'))
        except (ValueError, TypeError):
            messages.error(request, _('El orden debe ser un número válido.'))
    
    # Redirigir de vuelta a la página de navegación de videos
    return redirect('course_video_navigation', slug=video.course.slug, video_id=video_id)

@method_decorator(login_required, name='dispatch')
class PDFViewerView(View):
    def get(self, request, document_id):
        document = get_object_or_404(Upload, id=document_id)
        file_path = os.path.join(settings.MEDIA_ROOT, str(document.file))
        
        if not os.path.exists(file_path):
            raise Http404("El archivo no existe")
            
        response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="{}"'.format(os.path.basename(file_path))
        return response

@method_decorator(login_required, name='dispatch')
class PDFDownloadView(View):
    def get(self, request, document_id):
        document = get_object_or_404(Upload, id=document_id)
        file_path = os.path.join(settings.MEDIA_ROOT, str(document.file))
        
        if not os.path.exists(file_path):
            messages.error(request, "El archivo no existe o no está disponible.")
            return redirect('course_video_navigation', slug=document.course.slug)
            
        response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(os.path.basename(file_path))
        return response
