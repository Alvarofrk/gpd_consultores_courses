import os 
import io
import locale
from datetime import datetime, timedelta
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape,A4
from django.http import FileResponse, Http404, HttpResponse 
from django.db.models import Max
from django.utils.translation import gettext as _ 
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from babel.dates import format_datetime
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from babel.dates import format_datetime
from .models import Sitting 
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .forms import AnexoForm
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from accounts.decorators import lecturer_required
from .forms import (
    EssayForm,
    MCQuestionForm,
    MCQuestionFormSet,
    QuestionForm,
    QuizAddForm,
)
from .models import (
    Course,
    EssayQuestion,
    MCQuestion,
    Progress,
    Question,
    Quiz,
    Sitting,
)


# ########################################################
# Quiz Views 
# ########################################################
# def generar_certificado(request, sitting_id):
#     # Ruta de la plantilla de certificado en la carpeta `static/pdfs`
#     plantilla_path = os.path.join(settings.BASE_DIR, 'static', 'pdfs', 'certificado_template.pdf')

#     # Obtener el examen y validar que el usuario tiene permiso
#     sitting = get_object_or_404(Sitting, id=sitting_id, user=request.user)
    
#     # Verifica la puntuación antes de continuar
#     if sitting.get_percent_correct <= 80:
#         raise Http404("No se puede generar el certificado, la puntuación es menor al 80%.")

#     # Crear un buffer de memoria para el contenido que vamos a superponer
#     buffer = io.BytesIO()
#     p = canvas.Canvas(buffer, pagesize=landscape(A4))
#     ancho_pagina, alto_pagina = landscape(A4)
#     # Añadir el contenido de texto sobre la plantilla
#     # Ajusta la fuente, tamaño y color del texto
#     p.setFont("Helvetica-Bold", 30)  # Aumenta el tamaño de la fuente
#     p.setFillColorRGB(0.85, 0.64, 0.13)  # Color dorado en RGB


#     # Ajusta la posición del texto más abajo y centra el texto
#     p.drawCentredString(ancho_pagina / 2, 315, f"{request.user.first_name} {request.user.last_name}")
#     #p.drawCentredString(300, 370, f"Título del Examen: {sitting.quiz.title}")
#     p.setFillColorRGB(0.051, 0.231, 0.4)
#     p.setFont("Helvetica-Bold", 14)
#     p.drawCentredString(479, 198, f"{int(sitting.get_percent_correct / 5)}")
    
#     #locale.setlocale(locale.LC_TIME, 'es_ES.utf8')
#     #fecha_actual = datetime.now().strftime("%d de %B del %Y")
#     fecha_actual = format_datetime(
#         datetime.now(),
#         "d 'de' MMMM 'del' y",
#         locale='es'
#     )
#      # Formato dd/mm/yyyy
#     p.drawString(585, 220, f"{fecha_actual}")  # Ajusta la posición según sea necesario

#     p.setFont("Helvetica", 16)
#     p.setFillColorRGB(0.051, 0.231, 0.4)  # Color negro
#     p.drawString(485, 273, f"{request.user.username}")  

#     # Finalizar el contenido del buffer
#     p.showPage()
#     p.save()
#     buffer.seek(0)

#     # Cargar la plantilla de certificado
#     plantilla_pdf = PdfReader(plantilla_path)
#     pagina_plantilla = plantilla_pdf.pages[0]

#     # Crear un nuevo PDF con la plantilla y el contenido superpuesto
#     contenido_pdf = PdfReader(buffer)
#     writer = PdfWriter()
    
#     # Superponer la plantilla y el contenido nuevo
#     pagina_plantilla.merge_page(contenido_pdf.pages[0])
#     writer.add_page(pagina_plantilla)

#     # Guardar el PDF combinado en un nuevo buffer
#     resultado = io.BytesIO()
#     writer.write(resultado)
#     resultado.seek(0)

#     # Devolver el PDF combinado como respuesta
#     return FileResponse(resultado, as_attachment=True, filename='certificado.pdf')

# views.py

# views.py

# views.py

def generar_certificado(request, sitting_id):
    # Ruta de la plantilla de certificado en la carpeta `static/pdfs`
    plantilla_path = os.path.join(settings.BASE_DIR, 'static', 'pdfs', 'certificado_template.pdf')

    # Obtener el examen y validar que el usuario tiene permiso
    sitting = get_object_or_404(Sitting, id=sitting_id, user=request.user)

    # Datos comunes
    nombre_estudiante = f"{request.user.first_name} {request.user.last_name}"
    puntaje = int(sitting.get_percent_correct / 5)
    fecha_aprobacion_formateada = obtener_fecha_aprobacion(sitting)

    nombre_usuario = request.user.username
    certificate_code = sitting.certificate_code

    # Valores por defecto para las posiciones
    pos_nombre_estudiante = 305
    pos_puntaje = (479, 198)
    pos_fecha = (585, 220)
    pos_nombre_usuario = (485, 273)
    pos_codigo_certificado = (679, 466)

    # Determinar la plantilla de certificado según el código del curso
    if sitting.quiz.course.code == "0001":
        plantilla_path = os.path.join(settings.BASE_DIR, 'static', 'pdfs', 'certificado_0001.pdf')
        pos_puntaje = (728, 188)
        pos_fecha = (140, 188)
    elif sitting.quiz.course.code == "0002":
        plantilla_path = os.path.join(settings.BASE_DIR, 'static', 'pdfs', 'certificado_0002.pdf')
        pos_puntaje = (138, 167)
        pos_fecha = (230, 188)
    elif sitting.quiz.course.code == "0003":
        plantilla_path = os.path.join(settings.BASE_DIR, 'static', 'pdfs', 'certificado_0003.pdf')
        pos_puntaje = (738, 188)
        pos_fecha = (110, 188)
    elif sitting.quiz.course.code == "0004":
        plantilla_path = os.path.join(settings.BASE_DIR, 'static', 'pdfs', 'certificado_0004.pdf')
        pos_puntaje = (329, 188)
        pos_fecha = (397, 210)
    elif sitting.quiz.course.code == "0005":
        plantilla_path = os.path.join(settings.BASE_DIR, 'static', 'pdfs', 'certificado_0005.pdf')
        pos_puntaje = (702, 190)
        pos_fecha = (111, 190)
    elif sitting.quiz.course.code == "0006":
        plantilla_path = os.path.join(settings.BASE_DIR, 'static', 'pdfs', 'certificado_0006.pdf')
        pos_puntaje = (463, 184)
        pos_fecha = (561, 206)
    elif sitting.quiz.course.code == "0007":
        plantilla_path = os.path.join(settings.BASE_DIR, 'static', 'pdfs', 'certificado_0007.pdf')
        pos_puntaje = (331, 183)
        pos_fecha = (380, 205)
    elif sitting.quiz.course.code == "0008":
        plantilla_path = os.path.join(settings.BASE_DIR, 'static', 'pdfs', 'certificado_0008.pdf')
        pos_puntaje = (329, 183)
        pos_fecha = (461, 205)
    elif sitting.quiz.course.code == "0009":
        plantilla_path = os.path.join(settings.BASE_DIR, 'static', 'pdfs', 'certificado_0009.pdf')
        pos_puntaje = (465, 184.5)
        pos_fecha = (565, 206)
    else:
        # Si no hay un certificado específico, usar el certificado_template.pdf
        plantilla_path = os.path.join(settings.BASE_DIR, 'static', 'pdfs', 'certificado_template.pdf')
        pos_nombre_estudiante = 430

    # Verificar si el archivo existe
    if not os.path.exists(plantilla_path):
        # Si no existe, usar el certificado_template.pdf como respaldo
        plantilla_path = os.path.join(settings.BASE_DIR, 'static', 'pdfs', 'certificado_template.pdf')
        if not os.path.exists(plantilla_path):
            raise Http404("No se encontró la plantilla del certificado.")

    # Crear un buffer de memoria para el contenido que vamos a superponer
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=landscape(A4))
    ancho_pagina, alto_pagina = landscape(A4)

    # Mantenemos los mismos colores y valores que usas en tu plantilla original
    p.setFont("Helvetica-Bold", 30)
    p.setFillColorRGB(0.85, 0.64, 0.13)  # Color dorado (como en tu plantilla original)
    
    # Centrar el nombre del estudiante en el eje X
    p.drawCentredString(ancho_pagina / 2, pos_nombre_estudiante, nombre_estudiante)

    # Puntaje, fecha y nombre de usuario con posiciones fijas en ambos ejes
    p.setFillColorRGB(0.051, 0.231, 0.4)  # Color azul (como en tu plantilla original)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(pos_puntaje[0], pos_puntaje[1], f"{puntaje}")

    # Fecha
    p.setFont("Helvetica", 16)
    p.setFillColorRGB(0.051, 0.231, 0.4)  # Color azul (como en tu plantilla original)
    p.drawString(pos_fecha[0], pos_fecha[1], f"{fecha_aprobacion_formateada}")

    # Nombre de usuario
    p.setFont("Helvetica", 16)
    p.setFillColorRGB(0.051, 0.231, 0.4)  # Color azul (como en tu plantilla original)
    p.drawString(pos_nombre_usuario[0], pos_nombre_usuario[1], f"{nombre_usuario}")

    # Código del certificado
    p.setFont("Helvetica-Bold", 16)
    p.setFillColorRGB(0.051, 0.231, 0.4)  # Color azul (como en tu plantilla original)
    p.drawString(pos_codigo_certificado[0], pos_codigo_certificado[1], f"{certificate_code}")

    # Finalizar el contenido del buffer
    p.showPage()
    p.save()
    buffer.seek(0)

    # Cargar la plantilla del certificado
    plantilla_pdf = PdfReader(plantilla_path)
    pagina_plantilla = plantilla_pdf.pages[0]

    # Crear un nuevo PDF con la plantilla y el contenido superpuesto
    contenido_pdf = PdfReader(buffer)
    writer = PdfWriter()
    pagina_plantilla.merge_page(contenido_pdf.pages[0])
    writer.add_page(pagina_plantilla)

    # Guardar el PDF combinado en un nuevo buffer
    resultado = io.BytesIO()
    writer.write(resultado)
    resultado.seek(0)

    # Devolver el PDF combinado como respuesta
    return FileResponse(resultado, as_attachment=True, filename='certificado.pdf')
    
def anexo_form(request, sitting_id):
    if request.method == 'POST':
        form = AnexoForm(request.POST)
        if form.is_valid():
            # Obtener los datos del formulario
            fecha_ingreso = form.cleaned_data['fecha_ingreso']
            ocupacion = form.cleaned_data['ocupacion']
            area_trabajo = form.cleaned_data['area_trabajo']
            empresa = form.cleaned_data['empresa']  # Nuevo campo
            distrito = form.cleaned_data['distrito']  # Nuevo campo
            provincia = form.cleaned_data['provincia']  # Nuevo campo

            # Generar el anexo con los datos del formulario
            return generar_anexo4(request, sitting_id, fecha_ingreso, ocupacion, area_trabajo, empresa, distrito, provincia)
    else:
        form = AnexoForm()

    return render(request, 'quiz/anexo_form.html', {'form': form})

def generar_anexo4(request, sitting_id, fecha_ingreso, ocupacion, area_trabajo, empresa, distrito, provincia):
    # Obtener el examen y validar que el usuario tiene permiso
    sitting = get_object_or_404(Sitting, id=sitting_id, user=request.user)

    # Obtener la fecha de aprobación
    fecha_aprobacion = obtener_fecha_aprobacion(sitting)

 
    # Ruta del anexo
    anexo_path = os.path.join(settings.BASE_DIR, 'static', 'pdfs', 'anexo4.pdf')

    # Crear un buffer para el anexo
    buffer_anexo = io.BytesIO()
    p_anexo = canvas.Canvas(buffer_anexo, pagesize=A4)  # Cambiar a A4 para orientación vertical
    ancho_pagina_anexo, alto_pagina_anexo = A4  # Obtener dimensiones de A4 en vertical

    # Personaliza el contenido del anexo
    p_anexo.setFont("Helvetica", 11)  # Cambiar a un tamaño de fuente más pequeño
    p_anexo.setFillColorRGB(0, 0, 0)  # Color negro

    #mifuente nueva para firmas
    pdfmetrics.registerFont(TTFont('MiFuenteCursiva', os.path.join(settings.BASE_DIR, 'static', 'fonts', 'MiFuenteCursiva.ttf')))

    # Dibujar el nombre del usuario
    p_anexo.drawString(370, alto_pagina_anexo - 150, f"{sitting.user.first_name} {sitting.user.last_name}")
    
    # Dibujar el DNI (nombre de usuario)
    p_anexo.drawString(475, alto_pagina_anexo - 193, f"{sitting.user.username}")

    # Agregar los datos del formulario
    p_anexo.drawString(403, alto_pagina_anexo - 171.5, f"{fecha_ingreso}")
    p_anexo.drawString(379, alto_pagina_anexo - 213, f"{ocupacion}")
    p_anexo.drawString(400, alto_pagina_anexo - 233.5, f"{area_trabajo}")

    # Agregar los nuevos datos
    p_anexo.drawString(126.5, alto_pagina_anexo -171.5, f"{empresa}")
    p_anexo.drawString(68.2, alto_pagina_anexo - 214, f"{distrito}")
    p_anexo.drawString(79, alto_pagina_anexo - 235, f"{provincia}")
    
    # Agregar la fecha de aprobación sin formatear
    p_anexo.drawString(391, alto_pagina_anexo - 641, f"{fecha_aprobacion}")

    # Usar la fuente personalizada para la firma
    p_anexo.setFont("MiFuenteCursiva", 13)  # Cambiar a la fuente personalizada
    p_anexo.drawString(69, 115, f"{sitting.user.first_name} {sitting.user.last_name}")  # Ajusta la posición según sea necesario

    # Finalizar el contenido del buffer del anexo
    p_anexo.showPage()
    p_anexo.save()
    buffer_anexo.seek(0)

    # Cargar el anexo
    anexo_pdf = PdfReader(anexo_path)
    pagina_anexo = anexo_pdf.pages[0]

    # Crear un nuevo PDF con el contenido del anexo
    contenido_anexo_pdf = PdfReader(buffer_anexo)
    writer_anexo = PdfWriter()
    pagina_anexo.merge_page(contenido_anexo_pdf.pages[0])
    writer_anexo.add_page(pagina_anexo)

    # Guardar el PDF combinado en un nuevo buffer
    resultado_anexo = io.BytesIO()
    writer_anexo.write(resultado_anexo)
    resultado_anexo.seek(0)

    # Devolver el PDF del anexo como respuesta
    return FileResponse(resultado_anexo, as_attachment=True, filename='anexo4.pdf')



def obtener_fecha_aprobacion(exam):
    # Obtener la fecha de aprobación
    fecha_aprobacion = exam.fecha_aprobacion

    # Crear un diccionario para los nombres de los meses
    meses = {
        1: "enero",
        2: "febrero",
        3: "marzo",
        4: "abril",
        5: "mayo",
        6: "junio",
        7: "julio",
        8: "agosto",
        9: "septiembre",
        10: "octubre",
        11: "noviembre",
        12: "diciembre"
    }

    # Formatear el día con un cero delante si es necesario
    dia = f"{fecha_aprobacion.day:02d}"  # Formato con cero delante
    mes = meses[fecha_aprobacion.month]  # Obtener el nombre del mes
    año = fecha_aprobacion.year

    # Crear el string formateado
    return f"{dia} de {mes} del {año}"

def descargar_tabla_pdf(request):
    """Genera un PDF con la tabla de resultados de los exámenes"""
    if not request.user.is_authenticated:
        return redirect('login')

    # Obtener los exámenes del usuario y agrupar por curso para obtener la nota más alta
    exams = Sitting.objects.filter(user=request.user, complete=True).order_by('-end')
    
    # Crear el PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#1a237e'),  # Azul marino
        alignment=1  # Centrado
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=20,
        textColor=colors.HexColor('#1a237e'),
        alignment=1
    )
    
    # Título del documento
    elements.append(Paragraph("CONSOLIDADO DE CERTIFICADOS", title_style))
    
    # Información del usuario
    user_info = [
        f"Nombre: {request.user.get_full_name}",
        f"Usuario: {request.user.username}",
        f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    ]
    
    for info in user_info:
        elements.append(Paragraph(info, styles['Normal']))
    
    elements.append(Spacer(1, 30))
    
    # Tabla de resultados - solo mostrar la nota más alta de cada curso
    data = [['Curso', 'Nota', '%', 'Estado', 'Fecha Aprobación', 'Fecha Caducidad']]
    
    # Agrupar exámenes por curso y obtener la nota más alta
    cursos_dict = {}
    for exam in exams:
        curso_id = exam.quiz.course.id
        if curso_id not in cursos_dict or exam.get_percent_correct > cursos_dict[curso_id].get_percent_correct:
            cursos_dict[curso_id] = exam
    
    # Agregar solo los exámenes con la nota más alta
    for exam in cursos_dict.values():
        if exam.get_percent_correct >= 80:  # Solo mostrar si aprobó
            data.append([
                exam.quiz.course.title,
                str(exam.current_score * 2),
                f"{exam.get_percent_correct}%",
                "Completado",
                exam.fecha_aprobacion.strftime('%d/%m/%Y') if exam.fecha_aprobacion else "No disponible",
                (exam.fecha_aprobacion + timedelta(days=365)).strftime('%d/%m/%Y') if exam.fecha_aprobacion else "No disponible"
            ])
    
    # Estilo de la tabla con más espacio
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),  # Azul marino para el encabezado
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e8eaf6')]),  # Filas alternadas
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),  # Más espacio a la izquierda
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),  # Más espacio a la derecha
        ('TOPPADDING', (0, 0), (-1, -1), 8),     # Más espacio arriba
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),  # Más espacio abajo
    ])
    
    # Crear la tabla con columnas más anchas
    table = Table(data, colWidths=[200, 80, 60, 100, 120, 120])
    table.setStyle(table_style)
    elements.append(table)
    
    # Pie de página
    elements.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.gray,
        alignment=1
    )
    elements.append(Paragraph("Este documento es generado automáticamente por el sistema de gestión de aprendizaje", footer_style))
    
    # Construir el PDF
    doc.build(elements)
    
    # Preparar la respuesta
    buffer.seek(0)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="consolidado_certificados_{request.user.username}.pdf"'
    response.write(buffer.getvalue())
    buffer.close()
    
    return response


@method_decorator([login_required, lecturer_required], name="dispatch")
class QuizCreateView(CreateView):
    model = Quiz
    form_class = QuizAddForm
    template_name = "quiz/quiz_form.html"

    def get_initial(self):
        initial = super().get_initial()
        course = get_object_or_404(Course, slug=self.kwargs["slug"])
        initial["course"] = course
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["course"] = get_object_or_404(Course, slug=self.kwargs["slug"])
        return context

    def form_valid(self, form):
        form.instance.course = get_object_or_404(Course, slug=self.kwargs["slug"])
        with transaction.atomic():
            self.object = form.save()
            return redirect(
                "mc_create", slug=self.kwargs["slug"], quiz_id=self.object.id
            )


@method_decorator([login_required, lecturer_required], name="dispatch")
class QuizUpdateView(UpdateView):
    model = Quiz
    form_class = QuizAddForm
    template_name = "quiz/quiz_form.html"

    def get_object(self, queryset=None):
        return get_object_or_404(Quiz, pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["course"] = get_object_or_404(Course, slug=self.kwargs["slug"])
        return context

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            return redirect("quiz_index", self.kwargs["slug"])


@login_required
@lecturer_required
def quiz_delete(request, slug, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    quiz.delete()
    messages.success(request, "Quiz successfully deleted.")
    return redirect("quiz_index", slug=slug)


@login_required
def quiz_list(request, slug):
    course = get_object_or_404(Course, slug=slug)
    quizzes = Quiz.objects.filter(course=course).order_by("-timestamp")
    return render(
        request, "quiz/quiz_list.html", {"quizzes": quizzes, "course": course}
    )


# ########################################################
# Multiple Choice Question Views
# ########################################################


@method_decorator([login_required, lecturer_required], name="dispatch")
class MCQuestionCreate(CreateView):
    model = MCQuestion
    form_class = MCQuestionForm
    template_name = "quiz/mcquestion_form.html"

    # def get_form_kwargs(self):
    #     kwargs = super().get_form_kwargs()
    #     kwargs["quiz"] = get_object_or_404(Quiz, id=self.kwargs["quiz_id"])
    #     return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["course"] = get_object_or_404(Course, slug=self.kwargs["slug"])
        context["quiz_obj"] = get_object_or_404(Quiz, id=self.kwargs["quiz_id"])
        context["quiz_questions_count"] = Question.objects.filter(
            quiz=self.kwargs["quiz_id"]
        ).count()
        if self.request.method == "POST":
            context["formset"] = MCQuestionFormSet(self.request.POST)
        else:
            context["formset"] = MCQuestionFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]
        if formset.is_valid():
            with transaction.atomic():
                # Save the MCQuestion instance without committing to the database yet
                self.object = form.save(commit=False)
                self.object.save()

                # Retrieve the Quiz instance
                quiz = get_object_or_404(Quiz, id=self.kwargs["quiz_id"])

                # set the many-to-many relationship
                self.object.quiz.add(quiz)

                # Save the formset (choices for the question)
                formset.instance = self.object
                formset.save()

                if "another" in self.request.POST:
                    return redirect(
                        "mc_create",
                        slug=self.kwargs["slug"],
                        quiz_id=self.kwargs["quiz_id"],
                    )
                return redirect("quiz_index", slug=self.kwargs["slug"])
        else:
            return self.form_invalid(form)


# ########################################################
# Quiz Progress and Marking Views
# ########################################################


@method_decorator([login_required], name="dispatch")
class QuizUserProgressView(TemplateView):
    template_name = "quiz/progress.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        progress, _ = Progress.objects.get_or_create(user=self.request.user)
        context["cat_scores"] = progress.list_all_cat_scores
        context["exams"] = progress.show_exams()
        context["exams_counter"] = context["exams"].count()
        return context


@method_decorator([login_required, lecturer_required], name="dispatch")
class QuizMarkingList(ListView):
    model = Sitting
    template_name = "quiz/quiz_marking_list.html"

    def get_queryset(self):
        queryset = Sitting.objects.filter(complete=True)
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                quiz__course__allocated_course__lecturer__pk=self.request.user.id
            )
        quiz_filter = self.request.GET.get("quiz_filter")
        if quiz_filter:
            queryset = queryset.filter(quiz__title__icontains=quiz_filter)
        user_filter = self.request.GET.get("user_filter")
        if user_filter:
            queryset = queryset.filter(user__username__icontains=user_filter)
        return queryset


@method_decorator([login_required, lecturer_required], name="dispatch")
class QuizMarkingDetail(DetailView):
    model = Sitting
    template_name = "quiz/quiz_marking_detail.html"

    def post(self, request, *args, **kwargs):
        sitting = self.get_object()
        question_id = request.POST.get("qid")
        if question_id:
            question = Question.objects.get_subclass(id=int(question_id))
            if int(question_id) in sitting.get_incorrect_questions:
                sitting.remove_incorrect_question(question)
            else:
                sitting.add_incorrect_question(question)
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["questions"] = self.object.get_questions(with_answers=True)
        return context


# ########################################################
# Quiz Taking View
# ########################################################


@method_decorator([login_required], name="dispatch")
class QuizTake(FormView):
    form_class = QuestionForm
    template_name = "quiz/question.html"
    result_template_name = "quiz/result.html"

    def dispatch(self, request, *args, **kwargs):
        self.quiz = get_object_or_404(Quiz, slug=self.kwargs["slug"])
        self.course = get_object_or_404(Course, pk=self.kwargs["pk"])
        if not Question.objects.filter(quiz=self.quiz).exists():
            messages.warning(request, "Este examen no tiene preguntas disponibles")
            return redirect("quiz_index", slug=self.course.slug)

        self.sitting = Sitting.objects.user_sitting(
            request.user, self.quiz, self.course
        )
        
        # Si el usuario ya completó el examen, verificar si aprobó
        if not self.sitting:
            last_sitting = Sitting.objects.filter(
                user=request.user,
                quiz=self.quiz,
                course=self.course,
                complete=True
            ).order_by('-end').first()
            
            if last_sitting and last_sitting.get_percent_correct >= 80:
                messages.info(
                    request,
                    "Ya has aprobado este cuestionario.",
                )
                return redirect("quiz_index", slug=self.course.slug)
            elif last_sitting:
                # Si no aprobó, permitir reintentar
                self.sitting = Sitting.objects.create(
                    user=request.user,
                    quiz=self.quiz,
                    course=self.course
                )
            else:
                messages.info(
                    request,
                    "Ya has completado este cuestionario. Solo se permite un intento.",
                )
                return redirect("quiz_index", slug=self.course.slug)

        # Set self.question and self.progress here
        self.question = self.sitting.get_first_question()
        self.progress = self.sitting.progress()

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["question"] = self.question
        return kwargs

    def get_form_class(self):
        if isinstance(self.question, EssayQuestion):
            return EssayForm
        return self.form_class

    def form_valid(self, form):
        self.form_valid_user(form)
        if not self.sitting.get_first_question():
            return self.final_result_user()
        return super().get(self.request)

    def form_valid_user(self, form):
        progress, _ = Progress.objects.get_or_create(user=self.request.user)
        guess = form.cleaned_data["answers"]
        is_correct = self.question.check_if_correct(guess)

        if is_correct:
            self.sitting.add_to_score(1)
            progress.update_score(self.question, 1, 1)
        else:
            self.sitting.add_incorrect_question(self.question)
            progress.update_score(self.question, 0, 1)

        if not self.quiz.answers_at_end:
            self.previous = {
                "previous_answer": guess,
                "previous_outcome": is_correct,
                "previous_question": self.question,
                "answers": self.question.get_choices(),
                "question_type": {self.question.__class__.__name__: True},
            }
        else:
            self.previous = {}

        self.sitting.add_user_answer(self.question, guess)
        self.sitting.remove_first_question()

        # Update self.question and self.progress for the next question
        self.question = self.sitting.get_first_question()
        self.progress = self.sitting.progress()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["question"] = self.question
        context["quiz"] = self.quiz
        context["course"] = self.course
        if hasattr(self, "previous"):
            context["previous"] = self.previous
        if hasattr(self, "progress"):
            context["progress"] = self.progress
        return context

    def final_result_user(self):
        self.sitting.mark_quiz_complete()
        results = {
            "course": self.course,
            "quiz": self.quiz,
            "score": self.sitting.get_current_score,
            "max_score": self.sitting.get_max_score,
            "percent": self.sitting.get_percent_correct,
            "sitting": self.sitting,
            "previous": getattr(self, "previous", {}),
        }

        if self.quiz.answers_at_end:
            results["questions"] = self.sitting.get_questions(with_answers=True)
            results["incorrect_questions"] = self.sitting.get_incorrect_questions

        if (
            not self.quiz.exam_paper
            or self.request.user.is_superuser
            or self.request.user.is_lecturer
        ):
            self.sitting.delete()

        return render(self.request, self.result_template_name, results)
