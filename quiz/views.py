import os 
import io
import locale
from datetime import datetime, timedelta, date
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape,A4
from django.http import FileResponse, Http404, HttpResponse 
from django.db.models import Max, Count
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
from .forms import AnexoForm, ManualCertificateForm
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)

from accounts.decorators import lecturer_required, admin_required
from .forms import (
    EssayForm,
    MCQuestionForm,
    MCQuestionFormSet,
    QuestionForm,
    QuizAddForm,
    ManualCertificateForm,
)
from .models import (
    Course,
    EssayQuestion,
    MCQuestion,
    Progress,
    Question,
    Quiz,
    Sitting,
    ManualCertificate,
)
from django.views.decorators.csrf import csrf_exempt
import qrcode
from reportlab.lib.utils import ImageReader
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse

# Diccionario de posiciones por código de curso (disponible para todas las funciones)
POSICIONES_CERTIFICADOS = {
    "C01-IPERC":    {"pos_nombre": (490, 385), "pos_puntaje": (0, 0), "pos_fecha_aprobacion": (585, 200), "pos_fecha_aprobacion2": (464, 232), "pos_fecha_vencimiento": (630, 232), "pos_usuario": (555, 357), "pos_codigo": (815,335 ), "pos_qr": (750, 370)},
    "C02-PA":       {"pos_nombre": (490, 385), "pos_puntaje": (0, 0), "pos_fecha_aprobacion": (592, 205), "pos_fecha_aprobacion2": (490, 240), "pos_fecha_vencimiento": (660, 240), "pos_usuario": (555, 357), "pos_codigo": (806, 335), "pos_qr": (750, 370)},
    "C04-EC":      {"pos_nombre": (490, 401), "pos_puntaje": (0, 0), "pos_fecha_aprobacion": (585, 219), "pos_fecha_aprobacion2": (464, 252), "pos_fecha_vencimiento": (630, 252), "pos_usuario": (555, 372), "pos_codigo": (803,335.5 ), "pos_qr": (750, 370)},
    "C05-TC":      {"pos_nombre": (490, 402), "pos_puntaje": (0, 0), "pos_fecha_aprobacion": (585, 220), "pos_fecha_aprobacion2": (464, 256), "pos_fecha_vencimiento": (630, 256), "pos_usuario": (555, 372), "pos_codigo": (802,335 ), "pos_qr": (750, 370)},
    "C06-BE":      {"pos_nombre": (490, 402), "pos_puntaje": (0, 0), "pos_fecha_aprobacion": (585, 219), "pos_fecha_aprobacion2": (467, 255), "pos_fecha_vencimiento": (635, 255), "pos_usuario": (555, 372), "pos_codigo": (802,335.4 ), "pos_qr": (750, 370)},
    "C07-MI":      {"pos_nombre": (490, 437), "pos_puntaje": (0, 0), "pos_fecha_aprobacion": (585, 211.5), "pos_fecha_aprobacion2": (470, 245), "pos_fecha_vencimiento": (633, 245), "pos_usuario": (555, 405.5), "pos_codigo": (802.5,280 ), "pos_qr": (758.5, 320)},
    "C07-MPI":     {"pos_nombre": (490, 437), "pos_puntaje": (0, 0), "pos_fecha_aprobacion": (585, 211.5), "pos_fecha_aprobacion2": (470, 243.5), "pos_fecha_vencimiento": (633, 243.5), "pos_usuario": (555, 405.5), "pos_codigo": (804,273.5 ), "pos_qr": (757, 320)},
    "C07-MII":    {"pos_nombre": (490, 437), "pos_puntaje": (0, 0), "pos_fecha_aprobacion": (585, 211.5), "pos_fecha_aprobacion2": (470, 243.5), "pos_fecha_vencimiento": (633, 243.5), "pos_usuario": (555, 405.5), "pos_codigo": (807,279 ), "pos_qr": (757, 320)},
    "C07-MPII":   {"pos_nombre": (490, 437), "pos_puntaje": (0, 0), "pos_fecha_aprobacion": (585, 211.5), "pos_fecha_aprobacion2": (470, 243.5), "pos_fecha_vencimiento": (633, 243.5), "pos_usuario": (555, 405.5), "pos_codigo": (809.5,279.5 ), "pos_qr": (757, 320)},
    "C07-MPIII":    {"pos_nombre": (490, 437), "pos_puntaje": (0, 0), "pos_fecha_aprobacion": (585, 211.5), "pos_fecha_aprobacion2": (470, 243.5), "pos_fecha_vencimiento": (633, 243.5), "pos_usuario": (555, 405.5), "pos_codigo": (805.5,279.5 ), "pos_qr": (757, 320)},
    "C12-HS":      {"pos_nombre": (490, 385), "pos_puntaje": (0, 0), "pos_fecha_aprobacion": (585, 200), "pos_fecha_aprobacion2": (468, 232), "pos_fecha_vencimiento": (632, 232), "pos_usuario": (555, 357), "pos_codigo": (802,335 ), "pos_qr": (750, 370)},
    "C15-SE":      {"pos_nombre": (490, 401), "pos_puntaje": (0, 0), "pos_fecha_aprobacion": (582, 209), "pos_fecha_aprobacion2": (469, 236.5), "pos_fecha_vencimiento": (630, 236.5), "pos_usuario": (555, 373), "pos_codigo": (798,335.3 ), "pos_qr": (750, 370)},
    "C16-LI":      {"pos_nombre": (490, 385), "pos_puntaje": (0, 0), "pos_fecha_aprobacion": (585, 205), "pos_fecha_aprobacion2": (471, 237), "pos_fecha_vencimiento": (630, 237), "pos_usuario": (555, 357), "pos_codigo": (797.5,335 ), "pos_qr": (750, 370)},
    "C17-SEI":     {"pos_nombre": (490, 401), "pos_puntaje": (0, 0), "pos_fecha_aprobacion": (585, 224), "pos_fecha_aprobacion2": (464, 259.5), "pos_fecha_vencimiento": (630, 259.5), "pos_usuario": (555, 371), "pos_codigo": (800,335 ), "pos_qr": (750, 370)},
    "C19-TED":     {"pos_nombre": (490, 401), "pos_puntaje": (0, 0), "pos_fecha_aprobacion": (584, 215.5), "pos_fecha_aprobacion2": (466, 250.5), "pos_fecha_vencimiento": (630, 250.5), "pos_usuario": (555, 371), "pos_codigo": (809,335 ), "pos_qr": (750, 370)},
    "C63-UHP":     {"pos_nombre": (490, 401), "pos_puntaje": (0, 0), "pos_fecha_aprobacion": (588, 223.5), "pos_fecha_aprobacion2": (464, 261), "pos_fecha_vencimiento": (630, 261), "pos_usuario": (555, 371), "pos_codigo": (809,335.4 ), "pos_qr": (750, 370)},
    "C70-RTA":     {"pos_nombre": (490, 401), "pos_puntaje": (0, 0), "pos_fecha_aprobacion": (583, 223.5), "pos_fecha_aprobacion2": (464, 258.5), "pos_fecha_vencimiento": (630, 258.5), "pos_usuario": (555, 372), "pos_codigo": (805,335 ), "pos_qr": (750, 370)},
    "C24-TA":      {"pos_nombre": (490, 401), "pos_puntaje": (0, 0), "pos_fecha_aprobacion": (585, 221.8), "pos_fecha_aprobacion2": (464, 258.5), "pos_fecha_vencimiento": (625, 258.5), "pos_usuario": (555, 372), "pos_codigo": (788,326 ), "pos_qr": (750, 370)},
    "C22-MD":      {"pos_nombre": (475, 361), "pos_puntaje": (0, 0), "pos_fecha_aprobacion": (625, 183.4), "pos_fecha_aprobacion2": (555, 206.3), "pos_fecha_vencimiento": (681, 206.3), "pos_usuario": (565, 327), "pos_codigo": (795,295.5 ), "pos_qr": (750, 350)},
}

def formatear_fecha_larga(fecha):
    """Formatea una fecha en formato '30 de Julio del 2025'"""
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
    
    dia = fecha.day
    mes = meses[fecha.month]
    año = fecha.year
    
    return f"{dia} de {mes} del {año}"

def generar_certificado(request, sitting_id):
    # Obtener el examen y validar que el usuario tiene permiso
    sitting = get_object_or_404(Sitting, id=sitting_id, user=request.user)

    # Verificar que el examen esté completo y aprobado
    if not sitting.complete or sitting.get_percent_correct < 80:
        messages.error(request, "El examen debe estar completo y aprobado para generar el certificado.")
        return redirect('quiz_start', slug=sitting.quiz.url)

    # Obtener datos del certificado
    nombre_usuario = f"{sitting.user.first_name} {sitting.user.last_name}"
    # Convertir porcentaje a nota sobre 20 (igual que certificados manuales)
    porcentaje = sitting.get_percent_correct
    puntaje = round((porcentaje * 20) / 100)
    fecha_aprobacion = sitting.fecha_aprobacion
    fecha_vencimiento = fecha_aprobacion + timedelta(days=365)
    
    # Formatear fechas
    fecha_aprobacion_larga = formatear_fecha_larga(fecha_aprobacion)  # Nueva función para formato largo
    fecha_aprobacion_str = fecha_aprobacion.strftime("%d/%m/%Y")  # Formato corto para "Aprobado:" y "Vence:"
    fecha_vencimiento_str = fecha_vencimiento.strftime("%d/%m/%Y")
    
    # IMPORTANTE: El certificate_code ya está asignado permanentemente en el modelo
    # No debe incrementarse cada vez que se descarga el certificado
    # El código completo para verificación es: <código_curso>-<correlativo>
    certificate_code = f"{sitting.quiz.course.code}-{sitting.certificate_code}"

    # Usar las posiciones específicas del curso o las por defecto
    codigo = sitting.quiz.course.code
    posiciones = POSICIONES_CERTIFICADOS.get(codigo, {
        "pos_nombre": (305, 305),
        "pos_puntaje": (479, 198),
        "pos_fecha_aprobacion": (585, 220),
        "pos_fecha_aprobacion2": (585, 180),
        "pos_fecha_vencimiento": (585, 195),
        "pos_usuario": (485, 273),
        "pos_codigo": (679, 466),
        "pos_qr": (500, 50),
    })

    # Crear buffer para el contenido
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=landscape(A4))
    ancho_pagina, alto_pagina = landscape(A4)

    # Aplicar contenido con las posiciones específicas
    p.setFont("Helvetica-Bold", 24)
    p.setFillColorRGB(0.85, 0.64, 0.13)  # Color dorado
    p.drawCentredString(posiciones["pos_nombre"][0], posiciones["pos_nombre"][1], nombre_usuario)

    # Puntaje
    p.setFillColorRGB(0.051, 0.231, 0.4)  # Color azul
    p.setFont("Helvetica-Bold", 14)
    p.drawString(posiciones["pos_puntaje"][0], posiciones["pos_puntaje"][1], f"{puntaje}")

    # Fechas (aprobación y vencimiento) en tamaño más pequeño y color negro
    p.setFont("Helvetica", 12)
    p.setFillColorRGB(0, 0, 0)  # Negro
    p.drawString(posiciones["pos_fecha_aprobacion"][0], posiciones["pos_fecha_aprobacion"][1], f"{fecha_aprobacion_larga}")  # Formato largo
    p.drawString(posiciones["pos_fecha_aprobacion2"][0], posiciones["pos_fecha_aprobacion2"][1], f"Aprobado: {fecha_aprobacion_str}")  # Formato corto
    p.drawString(posiciones["pos_fecha_vencimiento"][0], posiciones["pos_fecha_vencimiento"][1], f"Vence: {fecha_vencimiento_str}")  # Formato corto

    # Username/DNI (no el nombre completo)
    p.setFont("Helvetica", 16)
    p.setFillColorRGB(0.051, 0.231, 0.4)  # Color azul (como en tu plantilla original)
    p.drawString(posiciones["pos_usuario"][0], posiciones["pos_usuario"][1], f"{sitting.user.username}")

    # Código del certificado (solo el correlativo)
    p.setFont("Helvetica-Bold", 12)
    p.setFillColorRGB(0, 0, 0)  # Negro
    p.drawString(posiciones["pos_codigo"][0], posiciones["pos_codigo"][1], f"{sitting.certificate_code}")

    # Generar la URL de verificación con el prefijo correcto
    url_verificacion = request.build_absolute_uri(
        f"/quiz/verificar-certificado/{certificate_code}/"
    )
    # Generar el QR en memoria
    qr = qrcode.make(url_verificacion)
    qr_buffer = io.BytesIO()
    qr.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    qr_img = ImageReader(qr_buffer)

    # Por ejemplo, en la esquina inferior derecha
    p.drawImage(qr_img, posiciones["pos_qr"][0], posiciones["pos_qr"][1], width=65, height=65)

    # Finalizar el contenido del buffer
    p.showPage()
    p.save()
    buffer.seek(0)

    # Cargar la plantilla del certificado
    plantilla_path = os.path.join(settings.BASE_DIR, 'static', 'pdfs', f'{codigo}.pdf')
    if not os.path.exists(plantilla_path):
        plantilla_path = os.path.join(settings.BASE_DIR, 'static', 'pdfs', 'certificado_template.pdf')

    # Verificar si el archivo existe
    if not os.path.exists(plantilla_path):
        # Si no existe, usar el certificado_template.pdf como respaldo
        plantilla_path = os.path.join(settings.BASE_DIR, 'static', 'pdfs', 'certificado_template.pdf')
        if not os.path.exists(plantilla_path):
            raise Http404("No se encontró la plantilla del certificado.")

    # Crear un nuevo PDF con la plantilla y el contenido superpuesto
    contenido_pdf = PdfReader(buffer)
    writer = PdfWriter()
    plantilla_pdf = PdfReader(plantilla_path)
    pagina_plantilla = plantilla_pdf.pages[0]
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
        try:
            form.instance.course = get_object_or_404(Course, slug=self.kwargs["slug"])
            with transaction.atomic():
                self.object = form.save()
                print(f"✅ Cuestionario creado exitosamente con ID: {self.object.id}")
                print(f"✅ Redirigiendo a: mc_create con slug={self.kwargs['slug']} y quiz_id={self.object.id}")
                
                # Verificar que la URL existe
                from django.urls import reverse
                try:
                    redirect_url = reverse("mc_create", kwargs={
                        "slug": self.kwargs["slug"], 
                        "quiz_id": self.object.id
                    })
                    print(f"✅ URL de redirección generada: {redirect_url}")
                except Exception as e:
                    print(f"❌ Error generando URL: {e}")
                    messages.error(self.request, f"Error en la redirección: {e}")
                    return redirect("quiz_index", slug=self.kwargs["slug"])
                
                return redirect("mc_create", slug=self.kwargs["slug"], quiz_id=self.object.id)
        except Exception as e:
            print(f"❌ Error en form_valid: {e}")
            messages.error(self.request, f"Error al crear el cuestionario: {e}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        print(f"❌ Formulario inválido. Errores: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                print(f"❌ Campo '{field}': {error}")
        return super().form_invalid(form)


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

    def dispatch(self, request, *args, **kwargs):
        print(f"🚀 MCQuestionCreate.dispatch() llamado")
        print(f"🚀 Parámetros: slug={kwargs.get('slug')}, quiz_id={kwargs.get('quiz_id')}")
        return super().dispatch(request, *args, **kwargs)

    # def get_form_kwargs(self):
    #     kwargs = super().get_form_kwargs()
    #     kwargs["quiz"] = get_object_or_404(Quiz, id=self.kwargs["quiz_id"])
    #     return kwargs

    def get_context_data(self, **kwargs):
        print(f"📋 MCQuestionCreate.get_context_data() llamado")
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
        print(f"📋 Contexto generado: course={context['course'].title}, quiz={context['quiz_obj'].title}")
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
        context["exams_counter"] = len(context["exams"])
        context["sitting_list"] = context["exams"]  # Asegura que sitting_list esté disponible para el template
        return context


@method_decorator([login_required, lecturer_required], name="dispatch")
class QuizMarkingList(ListView):
    model = Sitting
    template_name = "quiz/quiz_marking_list.html"
    paginate_by = 20  # 20 exámenes por página

    def get_queryset(self):
        queryset = Sitting.objects.filter(complete=True).order_by('-end')  # Ordenar por fecha más reciente
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Agregar información adicional para el template
        context['total_exams'] = self.get_queryset().count()
        context['current_page'] = self.request.GET.get('page', 1)
        return context


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
            # Buscar si existe algún registro aprobado
            approved_sitting = Sitting.objects.filter(
                user=request.user,
                quiz=self.quiz,
                course=self.course,
                complete=True,
                current_score__gte=self.quiz.pass_mark * self.quiz.get_max_score / 100
            ).first()
            if approved_sitting:
                messages.info(
                    request,
                    "Ya has aprobado este cuestionario.",
                )
                return redirect("quiz_index", slug=self.course.slug)
            else:
                # Eliminar todos los registros previos (aprobados o no)
                Sitting.objects.filter(
                    user=request.user,
                    quiz=self.quiz,
                    course=self.course
                ).delete()
                self.sitting = Sitting.objects.create(
                    user=request.user,
                    quiz=self.quiz,
                    course=self.course
                )

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

        return render(self.request, self.result_template_name, results)

@csrf_exempt
def verificar_certificado(request, codigo):
    """Vista unificada para verificar certificados (plataforma y manuales)"""
    # Buscar en certificados de plataforma por código completo
    sittings = Sitting.objects.filter(complete=True)
    for sitting in sittings:
        # Construir el código completo para comparar
        codigo_completo = f"{sitting.course.code}-{sitting.certificate_code}"
        if codigo_completo == codigo:
            # Convertir porcentaje a nota sobre 20 (igual que certificados manuales)
            porcentaje = sitting.get_percent_correct
            nota_sobre_20 = round((porcentaje * 20) / 100)
            
            return render(request, 'quiz/verificar_certificado.html', {
                'sitting': sitting,
                'nombre': f"{sitting.user.first_name} {sitting.user.last_name}",
                'curso': sitting.course.title,
                'nota': nota_sobre_20,
                'fecha': sitting.fecha_aprobacion,
                'codigo': codigo,
                'tipo': 'plataforma'
            })
    
    # Buscar en certificados manuales por código completo
    manual_certs = ManualCertificate.objects.filter(activo=True)
    for manual_cert in manual_certs:
        codigo_completo = f"{manual_cert.curso.code}-{manual_cert.certificate_code}"
        if codigo_completo == codigo:
            return render(request, 'quiz/verificar_certificado.html', {
                'certificate': manual_cert,
                'nombre': manual_cert.nombre_completo,
                'curso': manual_cert.curso.title,
                'nota': manual_cert.puntaje,
                'fecha': manual_cert.fecha_aprobacion,
                'codigo': codigo,
                'tipo': 'manual'
            })
    
    # No encontrado
    return render(request, 'quiz/certificado_no_encontrado.html', {'codigo': codigo})

@login_required
@admin_required
def generar_certificado_manual(request):
    """Vista para generar certificados manuales"""
    if request.method == 'POST':
        form = ManualCertificateForm(request.POST)
        if form.is_valid():
            certificate = form.save(commit=False)
            certificate.generado_por = request.user
            certificate.save()
            # Redirigir a la lista de certificados manuales en vez de descargar el PDF
            return redirect(reverse('listar_certificados_manuales'))
    else:
        form = ManualCertificateForm()
    return render(request, 'quiz/generar_certificado_manual.html', {
        'form': form,
        'title': 'Generar Certificado Manual'
    })

@login_required
@admin_required
def listar_certificados_manuales(request):
    """Vista para listar todos los certificados manuales"""
    certificados = ManualCertificate.objects.all()
    
    # Conteos globales
    hoy = date.today()
    en_30_dias = hoy + timedelta(days=30)
    total_certificados = certificados.count()
    activos = certificados.filter(activo=True, fecha_vencimiento__gte=hoy).count()
    por_vencer = certificados.filter(activo=True, fecha_vencimiento__gt=hoy, fecha_vencimiento__lte=en_30_dias).count()
    vencidos = certificados.filter(fecha_vencimiento__lt=hoy).count()
    
    # Filtros
    curso_filter = request.GET.get('curso')
    if curso_filter:
        certificados = certificados.filter(curso__code=curso_filter)
    
    estado_filter = request.GET.get('estado')
    if estado_filter == 'activos':
        certificados = certificados.filter(activo=True)
    elif estado_filter == 'vencidos':
        certificados = certificados.filter(fecha_vencimiento__lt=hoy)
    
    # Búsqueda
    search = request.GET.get('search')
    if search:
        certificados = certificados.filter(
            Q(nombre_completo__icontains=search) |
            Q(dni__icontains=search) |
            Q(certificate_code__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(certificados, 10)  # 10 certificados por página
    page = request.GET.get('page')
    try:
        certificados_page = paginator.page(page)
    except PageNotAnInteger:
        certificados_page = paginator.page(1)
    except EmptyPage:
        certificados_page = paginator.page(paginator.num_pages)
    
    return render(request, 'quiz/listar_certificados_manuales.html', {
        'certificados': certificados_page,
        'cursos': Course.objects.all(),
        'title': 'Certificados Manuales',
        'paginator': paginator,
        'page_obj': certificados_page,
        'is_paginated': certificados_page.has_other_pages(),
        'total_certificados': total_certificados,
        'activos': activos,
        'por_vencer': por_vencer,
        'vencidos': vencidos,
    })

@login_required
@admin_required
def descargar_certificado_manual(request, cert_id):
    """Vista para descargar certificado manual"""
    certificate = get_object_or_404(ManualCertificate, id=cert_id)
    # Usar la plantilla por defecto del curso o la plantilla template
    plantilla = f"{certificate.curso.code}.pdf"
    plantilla_path = os.path.join(settings.BASE_DIR, 'static', 'pdfs', plantilla)
    if not os.path.exists(plantilla_path):
        plantilla = 'certificado_template.pdf'
    return generar_pdf_certificado_manual(request, certificate, plantilla)

def generar_pdf_certificado_manual(request, certificate, plantilla_nombre):
    """Función para generar PDF de certificado manual"""
    # Datos del certificado
    nombre_estudiante = certificate.nombre_completo
    puntaje = certificate.puntaje
    fecha_aprobacion_larga = formatear_fecha_larga(certificate.fecha_aprobacion)  # Formato largo
    fecha_aprobacion_str = certificate.fecha_aprobacion.strftime("%d/%m/%Y")  # Formato corto
    fecha_vencimiento_str = certificate.fecha_vencimiento.strftime("%d/%m/%Y")
    dni = certificate.dni
    # Generar código único del certificado
    # IMPORTANTE: La numeración correlativa es individual por curso
    # El certificate_code almacena solo el número correlativo (ej: "001", "002")
    # El código completo mostrado en PDF es: <código_curso>-<correlativo> (ej: "C01-001")
    certificate_code = f"{certificate.curso.code}-{certificate.certificate_code}"
    # Usar las posiciones del curso o las por defecto
    codigo = certificate.curso.code
    posiciones = POSICIONES_CERTIFICADOS.get(codigo, {
        "pos_nombre": (305, 305),
        "pos_puntaje": (479, 198),
        "pos_fecha_aprobacion": (585, 220),
        "pos_fecha_aprobacion2": (585, 180),
        "pos_fecha_vencimiento": (585, 195),
        "pos_usuario": (485, 273),
        "pos_codigo": (679, 466),
        "pos_qr": (500, 50),
    })
    # Crear buffer para el contenido
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=landscape(A4))
    ancho_pagina, alto_pagina = landscape(A4)
    # Aplicar contenido con las mismas posiciones y estilos
    p.setFont("Helvetica-Bold", 24)
    p.setFillColorRGB(0.85, 0.64, 0.13)  # Color dorado
    p.drawCentredString(posiciones["pos_nombre"][0], posiciones["pos_nombre"][1], nombre_estudiante)
    # Puntaje
    p.setFillColorRGB(0.051, 0.231, 0.4)  # Color azul
    p.setFont("Helvetica-Bold", 14)
    p.drawString(posiciones["pos_puntaje"][0], posiciones["pos_puntaje"][1], f"{puntaje}")
    # Fechas
    p.setFont("Helvetica", 12)
    p.setFillColorRGB(0, 0, 0)  # Negro
    p.drawString(posiciones["pos_fecha_aprobacion"][0], posiciones["pos_fecha_aprobacion"][1], f"{fecha_aprobacion_larga}")  # Formato largo
    p.drawString(posiciones["pos_fecha_aprobacion2"][0], posiciones["pos_fecha_aprobacion2"][1], f"Aprobado: {fecha_aprobacion_str}")  # Formato corto
    p.drawString(posiciones["pos_fecha_vencimiento"][0], posiciones["pos_fecha_vencimiento"][1], f"Vence: {fecha_vencimiento_str}")  # Formato corto
    # DNI (no el nombre completo)
    p.setFont("Helvetica", 16)
    p.setFillColorRGB(0.051, 0.231, 0.4)  # Color azul
    p.drawString(posiciones["pos_usuario"][0], posiciones["pos_usuario"][1], f"{dni}")
    # Código del certificado (solo el correlativo)
    p.setFont("Helvetica-Bold", 12)
    p.setFillColorRGB(0, 0, 0)  # Negro
    p.drawString(posiciones["pos_codigo"][0], posiciones["pos_codigo"][1], f"{certificate.certificate_code}")
    # Generar QR con dominio completo
    url_verificacion = request.build_absolute_uri(f"/quiz/verificar-certificado/{certificate_code}/")
    qr = qrcode.make(url_verificacion)
    qr_buffer = io.BytesIO()
    qr.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    qr_img = ImageReader(qr_buffer)
    p.drawImage(qr_img, posiciones["pos_qr"][0], posiciones["pos_qr"][1], width=65, height=65)
    # Finalizar contenido
    p.showPage()
    p.save()
    buffer.seek(0)
    # Cargar plantilla seleccionada
    plantilla_path = os.path.join(settings.BASE_DIR, 'static', 'pdfs', plantilla_nombre)
    if not os.path.exists(plantilla_path):
        plantilla_path = os.path.join(settings.BASE_DIR, 'static', 'pdfs', 'certificado_template.pdf')
    # Crear PDF final
    contenido_pdf = PdfReader(buffer)
    writer = PdfWriter()
    plantilla_pdf = PdfReader(plantilla_path)
    pagina_plantilla = plantilla_pdf.pages[0]
    pagina_plantilla.merge_page(contenido_pdf.pages[0])
    writer.add_page(pagina_plantilla)
    resultado = io.BytesIO()
    writer.write(resultado)
    resultado.seek(0)
    nombre_sanitizado = certificate.nombre_completo.replace(" ", "_")
    nombre_curso_sanitizado = certificate.curso.title.replace(" ", "_")
    filename = f"{certificate.curso.code}-{certificate.certificate_code}-{nombre_curso_sanitizado}-{nombre_sanitizado}.pdf"
    return FileResponse(
        resultado, 
        as_attachment=True, 
        filename=filename
    )

class ManualCertificateUpdateView(UpdateView):
    model = ManualCertificate
    form_class = ManualCertificateForm
    template_name = 'quiz/editar_certificado_manual.html'
    context_object_name = 'certificate'

    def get_success_url(self):
        from django.urls import reverse
        return reverse('listar_certificados_manuales')

# ########################################################
# Dashboard de Certificados Views
# ########################################################

@method_decorator([login_required, lecturer_required], name="dispatch")
class CertificadosDashboardView(TemplateView):
    template_name = "quiz/certificados_dashboard.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener fecha actual y cálculos
        from datetime import date, timedelta
        hoy = date.today()
        en_30_dias = hoy + timedelta(days=30)
        inicio_mes = hoy.replace(day=1)
        
        # Función helper para convertir datetime a date
        def datetime_to_date(dt):
            if dt is None:
                return None
            if isinstance(dt, datetime):
                return dt.date()
            return dt
        
        # Filtrar por instructor si no es superusuario
        instructor_filter = {}
        if not self.request.user.is_superuser:
            instructor_filter = {
                'quiz__course__allocated_course__lecturer__pk': self.request.user.id
            }
        
        # Estadísticas de certificados automáticos (aprobados)
        sittings_aprobados = Sitting.objects.filter(
            complete=True,
            **instructor_filter
        ).select_related('quiz')
        
        # Filtrar por aprobación en Python ya que get_max_score es un método
        sittings_aprobados = [sitting for sitting in sittings_aprobados if sitting.get_percent_correct >= sitting.quiz.pass_mark]
        
        # Estadísticas de certificados manuales
        certificados_manuales = ManualCertificate.objects.filter(**instructor_filter)
        
        # Estadísticas generales
        context['total_automaticos'] = len(sittings_aprobados)
        context['total_manuales'] = certificados_manuales.count()
        context['total_certificados'] = context['total_automaticos'] + context['total_manuales']
        
        # Certificados activos (no vencidos)
        context['automaticos_activos'] = len([s for s in sittings_aprobados if s.fecha_aprobacion and datetime_to_date(s.fecha_aprobacion) >= hoy - timedelta(days=365)])
        context['manuales_activos'] = certificados_manuales.filter(
            activo=True,
            fecha_vencimiento__gte=hoy
        ).count()
        context['certificados_activos'] = context['automaticos_activos'] + context['manuales_activos']
        
        # Certificados vencidos
        context['automaticos_vencidos'] = len([s for s in sittings_aprobados if s.fecha_aprobacion and datetime_to_date(s.fecha_aprobacion) < hoy - timedelta(days=365)])
        context['manuales_vencidos'] = certificados_manuales.filter(
            fecha_vencimiento__lt=hoy
        ).count()
        context['certificados_vencidos'] = context['automaticos_vencidos'] + context['manuales_vencidos']
        
        # Certificados del mes actual
        context['automaticos_mes'] = len([s for s in sittings_aprobados if s.fecha_aprobacion and datetime_to_date(s.fecha_aprobacion) >= inicio_mes])
        context['manuales_mes'] = certificados_manuales.filter(
            fecha_generacion__gte=inicio_mes
        ).count()
        context['certificados_mes'] = context['automaticos_mes'] + context['manuales_mes']
        
        # Certificados por vencer (próximos 30 días)
        context['automaticos_por_vencer'] = len([s for s in sittings_aprobados if s.fecha_aprobacion and datetime_to_date(s.fecha_aprobacion) >= hoy - timedelta(days=335) and datetime_to_date(s.fecha_aprobacion) < hoy - timedelta(days=365)])
        context['manuales_por_vencer'] = certificados_manuales.filter(
            activo=True,
            fecha_vencimiento__gte=hoy,
            fecha_vencimiento__lte=en_30_dias
        ).count()
        context['por_vencer'] = context['automaticos_por_vencer'] + context['manuales_por_vencer']
        
        # Datos para gráficos y filtros
        context['datos_mensuales'] = self.get_datos_mensuales(instructor_filter)
        context['distribucion_cursos'] = self.get_distribucion_cursos(instructor_filter)
        context['certificados_recientes'] = self.get_certificados_recientes(instructor_filter)
        context['cursos_disponibles'] = self.get_cursos_disponibles(instructor_filter)
        
        return context
    
    def get_datos_mensuales(self, instructor_filter):
        """Obtener datos de certificados por mes (últimos 12 meses)"""
        from datetime import date, timedelta
        
        # Función helper para convertir datetime a date
        def datetime_to_date(dt):
            if dt is None:
                return None
            if isinstance(dt, datetime):
                return dt.date()
            return dt
        
        datos = []
        for i in range(12):
            fecha = date.today() - timedelta(days=30*i)
            inicio_mes = fecha.replace(day=1)
            fin_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            # Certificados automáticos del mes
            sittings_mes = Sitting.objects.filter(
                complete=True,
                fecha_aprobacion__gte=inicio_mes,
                fecha_aprobacion__lte=fin_mes,
                **instructor_filter
            ).select_related('quiz')
            
            automaticos = len([s for s in sittings_mes if s.get_percent_correct >= s.quiz.pass_mark])
            
            # Certificados manuales del mes
            manuales = ManualCertificate.objects.filter(
                fecha_generacion__gte=inicio_mes,
                fecha_generacion__lte=fin_mes,
                **instructor_filter
            ).count()
            
            datos.append({
                'mes': fecha.strftime('%b %Y'),
                'automaticos': automaticos,
                'manuales': manuales,
                'total': automaticos + manuales
            })
        
        return list(reversed(datos))
    
    def get_distribucion_cursos(self, instructor_filter):
        """Obtener distribución de certificados por curso"""
        from collections import Counter
        
        # Certificados automáticos por curso
        sittings_aprobados = Sitting.objects.filter(
            complete=True,
            **instructor_filter
        ).select_related('quiz', 'quiz__course')
        
        # Filtrar por aprobación y contar por curso
        cursos_automaticos = Counter()
        for sitting in sittings_aprobados:
            if sitting.get_percent_correct >= sitting.quiz.pass_mark:
                curso_title = sitting.quiz.course.title if sitting.quiz.course else 'Sin curso'
                cursos_automaticos[curso_title] += 1
        
        automaticos_por_curso = [{'quiz__course__title': curso, 'total': count} for curso, count in cursos_automaticos.most_common(10)]
        
        # Certificados manuales por curso
        manuales_por_curso = ManualCertificate.objects.filter(
            **instructor_filter
        ).values('curso__title').annotate(
            total=Count('id')
        ).order_by('-total')[:10]
        
        return {
            'automaticos': automaticos_por_curso,
            'manuales': list(manuales_por_curso)
        }
    
    def get_certificados_recientes(self, instructor_filter):
        """Obtener certificados más recientes"""
        from datetime import date, timedelta
        
        # Certificados automáticos recientes
        sittings_recientes = Sitting.objects.filter(
            complete=True,
            **instructor_filter
        ).select_related('user', 'quiz__course', 'quiz').order_by('-fecha_aprobacion')[:50]
        
        # Filtrar por aprobación y tomar los 10 más recientes
        automaticos_recientes = []
        for sitting in sittings_recientes:
            if sitting.get_percent_correct >= sitting.quiz.pass_mark:
                automaticos_recientes.append(sitting)
                if len(automaticos_recientes) >= 10:
                    break
        
        # Certificados manuales recientes
        manuales_recientes = ManualCertificate.objects.filter(
            **instructor_filter
        ).select_related('curso', 'generado_por').order_by('-fecha_generacion')[:10]
        
        return {
            'automaticos': automaticos_recientes,
            'manuales': manuales_recientes
        }
    
    def get_cursos_disponibles(self, instructor_filter):
        """Obtener lista de cursos disponibles para filtros"""
        from course.models import Course
        
        if self.request.user.is_superuser:
            cursos = Course.objects.all().order_by('title')
        else:
            # Para instructores, obtener cursos asignados
            cursos = Course.objects.filter(allocated_course__lecturer=self.request.user).order_by('title')
        
        return cursos


@method_decorator([login_required, lecturer_required], name="dispatch")
class CertificadosEstadisticasAjaxView(View):
    """Vista AJAX para cargar estadísticas por curso seleccionados"""
    
    def post(self, request, *args, **kwargs):
        from django.http import JsonResponse
        from course.models import Course
        from datetime import date, timedelta
        
        try:
            # Obtener IDs de cursos seleccionados
            curso_ids = request.POST.getlist('curso_ids[]')
            
            if not curso_ids:
                return JsonResponse({
                    'success': False,
                    'message': 'No se seleccionaron cursos'
                })
            
            # Filtrar por instructor si no es superusuario
            instructor_filter = {}
            if not request.user.is_superuser:
                instructor_filter = {
                    'quiz__course__allocated_course__lecturer__pk': request.user.id
                }
            
            # Obtener solo los cursos seleccionados
            if request.user.is_superuser:
                cursos = Course.objects.filter(id__in=curso_ids).order_by('title')
            else:
                cursos = Course.objects.filter(
                    id__in=curso_ids,
                    allocated_course__lecturer=request.user
                ).order_by('title')
            
            # Calcular estadísticas solo para los cursos seleccionados
            estadisticas = []
            hoy = date.today()
            
            for curso in cursos:
                # Certificados automáticos del curso
                sittings_curso = Sitting.objects.filter(
                    complete=True,
                    quiz__course=curso
                ).select_related('quiz', 'user')
                
                # Filtrar por aprobación
                sittings_aprobados = []
                for s in sittings_curso:
                    try:
                        if s.get_percent_correct >= s.quiz.pass_mark:
                            sittings_aprobados.append(s)
                    except Exception as e:
                        continue
                
                # Certificados manuales del curso
                certificados_manuales = ManualCertificate.objects.filter(curso=curso)
                
                # Calcular estadísticas
                total_automaticos = len(sittings_aprobados)
                total_manuales = certificados_manuales.count()
                total_curso = total_automaticos + total_manuales
                
                # Certificados activos (no vencidos)
                automaticos_activos = len([s for s in sittings_aprobados if s.fecha_aprobacion and s.fecha_aprobacion.date() >= hoy - timedelta(days=365)])
                manuales_activos = certificados_manuales.filter(activo=True, fecha_vencimiento__gte=hoy).count()
                total_activos = automaticos_activos + manuales_activos
                
                # Certificados vencidos
                automaticos_vencidos = len([s for s in sittings_aprobados if s.fecha_aprobacion and s.fecha_aprobacion.date() < hoy - timedelta(days=365)])
                manuales_vencidos = certificados_manuales.filter(fecha_vencimiento__lt=hoy).count()
                total_vencidos = automaticos_vencidos + manuales_vencidos
                
                # Último certificado
                ultimo_automatico = sittings_aprobados[-1] if sittings_aprobados else None
                ultimo_manual = certificados_manuales.order_by('-fecha_generacion').first()
                
                ultimo_certificado = None
                try:
                    if ultimo_automatico and ultimo_manual:
                        if ultimo_automatico.fecha_aprobacion > ultimo_manual.fecha_generacion:
                            usuario_nombre = ultimo_automatico.user.get_full_name() if ultimo_automatico.user else 'Usuario no disponible'
                            ultimo_certificado = {
                                'tipo': 'Automático',
                                'fecha': ultimo_automatico.fecha_aprobacion.strftime('%d/%m/%Y') if ultimo_automatico.fecha_aprobacion else None,
                                'usuario': usuario_nombre
                            }
                        else:
                            ultimo_certificado = {
                                'tipo': 'Manual',
                                'fecha': ultimo_manual.fecha_generacion.strftime('%d/%m/%Y') if ultimo_manual.fecha_generacion else None,
                                'usuario': ultimo_manual.nombre_completo
                            }
                    elif ultimo_automatico:
                        usuario_nombre = ultimo_automatico.user.get_full_name() if ultimo_automatico.user else 'Usuario no disponible'
                        ultimo_certificado = {
                            'tipo': 'Automático',
                            'fecha': ultimo_automatico.fecha_aprobacion.strftime('%d/%m/%Y') if ultimo_automatico.fecha_aprobacion else None,
                            'usuario': usuario_nombre
                        }
                    elif ultimo_manual:
                        ultimo_certificado = {
                            'tipo': 'Manual',
                            'fecha': ultimo_manual.fecha_generacion.strftime('%d/%m/%Y') if ultimo_manual.fecha_generacion else None,
                            'usuario': ultimo_manual.nombre_completo
                        }
                except Exception as e:
                    ultimo_certificado = {
                        'tipo': 'Error',
                        'fecha': None,
                        'usuario': 'Error al obtener datos'
                    }
                
                estadisticas.append({
                    'curso_id': curso.id,
                    'curso_titulo': curso.title,
                    'total_automaticos': total_automaticos,
                    'total_manuales': total_manuales,
                    'total_curso': total_curso,
                    'total_activos': total_activos,
                    'total_vencidos': total_vencidos,
                    'ultimo_certificado': ultimo_certificado
                })
            
            return JsonResponse({
                'success': True,
                'estadisticas': estadisticas
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al cargar estadísticas: {str(e)}'
            })
