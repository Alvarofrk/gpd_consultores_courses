import os 
import io
import locale
from datetime import datetime, timedelta, date
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape,A4
from django.http import FileResponse, Http404, HttpResponse 
from django.db.models import Max, Count, Q
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
from .models import Sitting, SittingAuditLog 
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .forms import AnexoForm, ManualCertificateForm, SittingDateUpdateForm
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
    "C55-SEN":      {"pos_nombre": (475, 361), "pos_puntaje": (0, 0), "pos_fecha_aprobacion": (625, 183.4), "pos_fecha_aprobacion2": (555, 206.3), "pos_fecha_vencimiento": (681, 206.3), "pos_usuario": (565, 327), "pos_codigo": (795,295.5 ), "pos_qr": (750, 350)},
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

def ajustar_tamano_nombre(nombre):
    """
    Ajusta el tamaño de fuente del nombre según su longitud
    Rangos: <=25, <=35, <=45, else
    """
    longitud = len(nombre.strip())
    
    if longitud <= 25:
        return 24  # Tamaño normal
    elif longitud <= 35:
        return 20  # Tamaño mediano
    elif longitud <= 45:
        return 16  # Tamaño pequeño
    else:
        return 14  # Tamaño muy pequeño

def generar_certificado(request, sitting_id):
    # FUNCIONALIDAD DESHABILITADA PARA PARTICIPANTES
    # Solo administradores pueden descargar certificados
    if not request.user.is_staff and not request.user.is_superuser:
        messages.info(request, "La descarga de certificados está disponible solo para administradores.")
        return redirect('quiz_progress')
    
    # Obtener el examen y validar permisos
    if request.user.is_staff or request.user.is_superuser:
        # Administradores pueden descargar cualquier certificado
        sitting = get_object_or_404(Sitting, id=sitting_id)
    else:
        # Participantes solo pueden descargar sus propios certificados
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
    # Ajustar tamaño de fuente según la longitud del nombre
    tamano_fuente = ajustar_tamano_nombre(nombre_usuario)
    p.setFont("Helvetica-Bold", tamano_fuente)
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

    # Generar nombre descriptivo del archivo
    nombre_usuario_sanitizado = nombre_usuario.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_").replace("*", "_").replace("?", "_").replace("\"", "_").replace("<", "_").replace(">", "_").replace("|", "_")
    nombre_curso_sanitizado = sitting.quiz.course.title.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_").replace("*", "_").replace("?", "_").replace("\"", "_").replace("<", "_").replace(">", "_").replace("|", "_")
    
    # Limitar longitud de nombres para evitar nombres de archivo muy largos
    if len(nombre_usuario_sanitizado) > 50:
        nombre_usuario_sanitizado = nombre_usuario_sanitizado[:50]
    if len(nombre_curso_sanitizado) > 50:
        nombre_curso_sanitizado = nombre_curso_sanitizado[:50]
    
    # Formato: {código_curso}-{número_certificado}-{nombre_curso}-{nombre_participante}.pdf
    filename = f"{sitting.quiz.course.code}-{sitting.certificate_code}-{nombre_curso_sanitizado}-{nombre_usuario_sanitizado}.pdf"

    # Devolver el PDF combinado como respuesta
    return FileResponse(resultado, as_attachment=True, filename=filename)
    
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
    template_name = "quiz/sitting_list.html"
    paginate_by = 20  # 20 exámenes por página

    def get_queryset(self):
        from django.db.models import Count, F, Q
        
        # OPTIMIZACIÓN: Usar select_related para eliminar N+1 queries
        # MODIFICACIÓN: Solo mostrar exámenes aprobados (completos = aprobados)
        # Nota: No podemos usar max_score directamente en ORM porque es un @property
        queryset = Sitting.objects.filter(complete=True).select_related(
            'user', 'quiz', 'quiz__course'
        ).prefetch_related('quiz__question_set').order_by('-end')
        
        # Filtro por instructor si no es superusuario
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                quiz__course__allocated_course__lecturer__pk=self.request.user.id
            )
        
        # OPTIMIZACIÓN: Anotar campos calculados para evitar consultas en template
        # CORREGIDO: Contar solo intentos completados del usuario para ese quiz específico
        queryset = queryset.annotate(
            # CORREGIDO: Contar intentos totales completados para este usuario y quiz específico
            # Usar el mismo quiz del sitting actual, no todos los quizzes del usuario
            total_attempts=Count(
                'user__sitting',
                filter=Q(quiz=F('quiz'), complete=True),
                distinct=True
            )
        )
        
        # Para approved_attempts, necesitamos calcularlo en Python después de obtener los datos
        # porque max_score es un @property que no se puede usar en ORM
        
        # OPTIMIZACIÓN: Usar filtros más eficientes
        quiz_filter = self.request.GET.get("quiz_filter")
        if quiz_filter:
            # Usar istartswith en lugar de icontains para mejor rendimiento
            queryset = queryset.filter(quiz__title__istartswith=quiz_filter)
        
        user_filter = self.request.GET.get("user_filter")
        if user_filter:
            # Usar istartswith en lugar de icontains para mejor rendimiento
            queryset = queryset.filter(user__username__istartswith=user_filter)
        
        return queryset

    def get_queryset_with_approved_attempts(self):
        """
        Obtiene el queryset optimizado, filtra solo exámenes aprobados y calcula approved_attempts
        CORREGIDO: Solo devuelve UN registro por usuario+quiz (unicidad real)
        """
        queryset = self.get_queryset()
        
        # Convertir a lista para poder iterar y filtrar aprobados
        sittings_list = list(queryset)
        
        # Filtrar solo exámenes aprobados y calcular approved_attempts
        # CORREGIDO: Implementar unicidad real - solo un registro por usuario+quiz
        approved_sittings = []
        certificados_unicos = set()
        
        for sitting in sittings_list:
            # Verificar si está aprobado usando la lógica del modelo
            if sitting.get_percent_correct >= sitting.quiz.pass_mark:
                # Crear clave única: usuario + quiz
                clave_unica = f"{sitting.user.id}_{sitting.quiz.id}"
                
                # Solo agregar si no hemos visto esta combinación antes
                if clave_unica not in certificados_unicos:
                    certificados_unicos.add(clave_unica)
                    
                    # CORREGIDO: Obtener todos los intentos del usuario para este quiz específico
                    user_quiz_attempts = Sitting.objects.filter(
                        user=sitting.user,
                        quiz=sitting.quiz,  # Solo este quiz específico
                        complete=True
                    ).order_by('start')
                    
                    # CORREGIDO: Contar cuántos están aprobados para este quiz específico
                    approved_count = 0
                    for attempt in user_quiz_attempts:
                        if attempt.get_percent_correct >= attempt.quiz.pass_mark:
                            approved_count += 1
                    
                    # CORREGIDO: Recalcular total_attempts para este quiz específico
                    sitting.total_attempts = user_quiz_attempts.count()
                    sitting.approved_attempts = approved_count
                    approved_sittings.append(sitting)
        
        return approved_sittings

    def get(self, request, *args, **kwargs):
        """
        Sobrescribir get para usar el queryset con solo exámenes aprobados
        """
        # Obtener el queryset con solo exámenes aprobados
        self.object_list = self.get_queryset_with_approved_attempts()
        
        # Aplicar paginación manualmente
        from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
        
        paginator = Paginator(self.object_list, self.paginate_by)
        page = request.GET.get('page')
        
        try:
            object_list = paginator.page(page)
        except PageNotAnInteger:
            object_list = paginator.page(1)
        except EmptyPage:
            object_list = paginator.page(paginator.num_pages)
        
        context = self.get_context_data(object_list=object_list)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        from django.core.cache import cache
        
        context = super().get_context_data(**kwargs)
        
        # CORREGIDO: Usar object_list (ya filtrado y único) en lugar de queryset
        # Eliminar caché que puede causar inconsistencias
        object_list = kwargs.get('object_list', [])
        
        # Calcular estadísticas correctas basadas en object_list
        total_exams = len(object_list) if hasattr(object_list, '__len__') else 0
        
        # Calcular usuarios únicos correctamente
        usuarios_unicos = set()
        if hasattr(object_list, '__iter__'):
            for sitting in object_list:
                usuarios_unicos.add(sitting.user.id)
        
        stats = {
            'total_exams': total_exams,
            'total_approved': total_exams,  # Todos son aprobados (ya filtrados)
            'total_failed': 0,  # No hay fallidos en esta vista
            'unique_users': len(usuarios_unicos),
            'current_page': self.request.GET.get('page', 1),
        }
        
        context.update(stats)
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
    # Ajustar tamaño de fuente según la longitud del nombre
    tamano_fuente = ajustar_tamano_nombre(nombre_estudiante)
    p.setFont("Helvetica-Bold", tamano_fuente)
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
        
        # Importar funciones unificadas de utilidades
        from .certificate_utils import (
            datetime_to_date, 
            is_certificate_active, 
            is_certificate_expired, 
            is_certificate_expiring_soon
        )
        
        # Sin filtrado por instructor - mostrar todos los certificados
        
        # Estadísticas de certificados automáticos (aprobados) - OPTIMIZADO CON ORM
        from django.db.models import F, Q, Count

        # Obtener sittings completados con información del quiz
        sittings_completados = Sitting.objects.filter(
            complete=True
        ).select_related('quiz', 'course', 'user')
        
        # Filtrar aprobados usando Python (ya que get_max_score es un método)
        # CORREGIDO: Solo incluir sittings que realmente aprobaron
        sittings_aprobados = []
        for sitting in sittings_completados:
            if sitting.get_percent_correct >= sitting.quiz.pass_mark:
                sittings_aprobados.append(sitting)
        
        # Estadísticas de certificados manuales
        certificados_manuales = ManualCertificate.objects.all()
        
        # Estadísticas generales
        # CORREGIDO: Solo contar un examen aprobado por usuario por quiz (evitar duplicados)
        certificados_unicos = set()
        for s in sittings_aprobados:
            if s.fecha_aprobacion:
                # Crear clave única: usuario + quiz
                clave_unica = f"{s.user.id}_{s.quiz.id}"
                certificados_unicos.add(clave_unica)
        
        context['total_automaticos'] = len(certificados_unicos)
        context['total_manuales'] = certificados_manuales.count()
        context['total_certificados'] = context['total_automaticos'] + context['total_manuales']
        
        # Certificados activos (no vencidos) - LÓGICA UNIFICADA
        # CORREGIDO: Solo contar certificados únicos que tienen fecha_aprobacion válida
        certificados_activos_unicos = set()
        for s in sittings_aprobados:
            if s.fecha_aprobacion and is_certificate_active(s, hoy):
                clave_unica = f"{s.user.id}_{s.quiz.id}"
                certificados_activos_unicos.add(clave_unica)
        
        automaticos_activos = len(certificados_activos_unicos)
        manuales_activos = len([c for c in certificados_manuales if is_certificate_active(c, hoy)])
        
        context['automaticos_activos'] = automaticos_activos
        context['manuales_activos'] = manuales_activos
        context['certificados_activos'] = automaticos_activos + manuales_activos
        
        # Certificados vencidos - LÓGICA UNIFICADA
        # CORREGIDO: Solo contar certificados únicos que tienen fecha_aprobacion válida
        certificados_vencidos_unicos = set()
        for s in sittings_aprobados:
            if s.fecha_aprobacion and is_certificate_expired(s, hoy):
                clave_unica = f"{s.user.id}_{s.quiz.id}"
                certificados_vencidos_unicos.add(clave_unica)
        
        automaticos_vencidos = len(certificados_vencidos_unicos)
        manuales_vencidos = len([c for c in certificados_manuales if is_certificate_expired(c, hoy)])
        
        context['automaticos_vencidos'] = automaticos_vencidos
        context['manuales_vencidos'] = manuales_vencidos
        context['certificados_vencidos'] = automaticos_vencidos + manuales_vencidos
        
        # Certificados del mes actual
        # CORREGIDO: Solo contar certificados únicos del mes
        certificados_mes_unicos = set()
        for s in sittings_aprobados:
            if s.fecha_aprobacion and datetime_to_date(s.fecha_aprobacion) >= inicio_mes:
                clave_unica = f"{s.user.id}_{s.quiz.id}"
                certificados_mes_unicos.add(clave_unica)
        
        context['automaticos_mes'] = len(certificados_mes_unicos)
        context['manuales_mes'] = certificados_manuales.filter(
            fecha_generacion__gte=inicio_mes
        ).count()
        context['certificados_mes'] = context['automaticos_mes'] + context['manuales_mes']
        
        # Certificados por vencer (próximos 30 días) - LÓGICA UNIFICADA
        # CORREGIDO: Solo contar certificados únicos que tienen fecha_aprobacion válida
        certificados_por_vencer_unicos = set()
        for s in sittings_aprobados:
            if s.fecha_aprobacion and is_certificate_expiring_soon(s, hoy, 30):
                clave_unica = f"{s.user.id}_{s.quiz.id}"
                certificados_por_vencer_unicos.add(clave_unica)
        
        automaticos_por_vencer = len(certificados_por_vencer_unicos)
        manuales_por_vencer = len([c for c in certificados_manuales if is_certificate_expiring_soon(c, hoy, 30)])
        
        context['automaticos_por_vencer'] = automaticos_por_vencer
        context['manuales_por_vencer'] = manuales_por_vencer
        context['por_vencer'] = automaticos_por_vencer + manuales_por_vencer
        
        # Datos para gráficos y filtros
        context['datos_mensuales'] = self.get_datos_mensuales(sittings_aprobados, certificados_manuales)
        context['distribucion_cursos'] = self.get_distribucion_cursos(sittings_aprobados)
        context['certificados_recientes'] = self.get_certificados_recientes(sittings_aprobados)
        
        # Cursos para el template (QuerySet) y para JavaScript (JSON)
        context['cursos_disponibles'] = self.get_cursos_disponibles()
        context['cursos_disponibles_json'] = self.get_cursos_disponibles_json()
        
        # Datos para la pestaña de cursos
        context.update(self.get_datos_cursos(sittings_aprobados, certificados_manuales))
        
        return context
    
    def get_datos_mensuales(self, sittings_aprobados, certificados_manuales):
        """Obtener datos de certificados por mes (últimos 12 meses)"""
        from datetime import date, timedelta
        
        datos = []
        for i in range(12):
            fecha = date.today() - timedelta(days=30*i)
            inicio_mes = fecha.replace(day=1)
            fin_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            # Certificados automáticos del mes (usar fecha_aprobacion)
            # CORREGIDO: Solo contar certificados únicos del mes
            certificados_mes_unicos = set()
            for sitting in sittings_aprobados:
                if sitting.fecha_aprobacion:
                    sitting_date = sitting.fecha_aprobacion.date() if hasattr(sitting.fecha_aprobacion, 'date') else sitting.fecha_aprobacion
                    if inicio_mes <= sitting_date <= fin_mes:
                        clave_unica = f"{sitting.user.id}_{sitting.quiz.id}"
                        certificados_mes_unicos.add(clave_unica)
            automaticos = len(certificados_mes_unicos)
            
            # Certificados manuales del mes
            manuales = 0
            for cert in certificados_manuales:
                if cert.fecha_generacion:
                    cert_date = cert.fecha_generacion.date() if hasattr(cert.fecha_generacion, 'date') else cert.fecha_generacion
                    if inicio_mes <= cert_date <= fin_mes:
                        manuales += 1
            
            datos.append({
                'mes': fecha.strftime('%b %Y'),
                'automaticos': automaticos,
                'manuales': manuales,
                'total': automaticos + manuales
            })
        
        return list(reversed(datos))
    
    def get_distribucion_cursos(self, sittings_aprobados):
        """Obtener distribución de certificados por curso"""
        from collections import Counter
        
        # Agrupar por curso
        # CORREGIDO: Solo contar certificados únicos por curso
        from collections import Counter
        cursos_automaticos = Counter()
        certificados_por_curso = set()
        for sitting in sittings_aprobados:
            clave_unica = f"{sitting.user.id}_{sitting.quiz.id}"
            if clave_unica not in certificados_por_curso:
                certificados_por_curso.add(clave_unica)
                cursos_automaticos[sitting.quiz.course.title] += 1
        
        automaticos_por_curso = [
            {'quiz__course__title': curso, 'total': total} 
            for curso, total in cursos_automaticos.most_common(10)
        ]
        
        # Certificados manuales por curso
        manuales_por_curso = ManualCertificate.objects.all().values('curso__title').annotate(
            total=Count('id')
        ).order_by('-total')[:10]
        
        return {
            'automaticos': list(automaticos_por_curso),
            'manuales': list(manuales_por_curso)
        }
    
    def get_certificados_recientes(self, sittings_aprobados):
        """Obtener certificados más recientes"""
        from datetime import date, timedelta
        
        # Certificados automáticos recientes - usar datos ya calculados
        # CORREGIDO: Solo incluir sittings únicos que realmente aprobaron y tienen fecha_aprobacion
        automaticos_recientes = []
        certificados_unicos = set()
        
        # Ordenar por fecha_aprobacion descendente
        sittings_ordenados = sorted(sittings_aprobados, key=lambda x: x.fecha_aprobacion or x.end, reverse=True)
        
        for sitting in sittings_ordenados:
            if sitting.fecha_aprobacion:
                clave_unica = f"{sitting.user.id}_{sitting.quiz.id}"
                if clave_unica not in certificados_unicos:
                    certificados_unicos.add(clave_unica)
                    automaticos_recientes.append(sitting)
                    if len(automaticos_recientes) >= 10:
                        break
        
        # Certificados manuales recientes
        manuales_recientes = ManualCertificate.objects.all().select_related('curso', 'generado_por').order_by('-fecha_generacion')[:10]
        
        return {
            'automaticos': automaticos_recientes,
            'manuales': manuales_recientes
        }
    
    def get_cursos_disponibles(self):
        """Obtener lista de cursos disponibles para el template"""
        from course.models import Course
        
        cursos = Course.objects.all().order_by('title')
        return cursos
    
    def get_cursos_disponibles_json(self):
        """Obtener lista de cursos disponibles para JavaScript (JSON)"""
        from course.models import Course
        import json
        
        cursos = Course.objects.all().order_by('title')
        
        # Serializar cursos con información adicional
        cursos_data = []
        for curso in cursos:
            # Verificar si el curso tiene exámenes (para certificados automáticos)
            tiene_examen = curso.quiz_set.exists()
            
            # Verificar si el curso tiene certificados manuales
            tiene_manuales = ManualCertificate.objects.filter(curso=curso).exists()
            
            cursos_data.append({
                'id': curso.id,
                'title': curso.title,
                'code': curso.code,
                'tiene_examen': tiene_examen,
                'tiene_manuales': tiene_manuales
            })
        
        return json.dumps(cursos_data)
    
    def get_datos_cursos(self, sittings_aprobados, certificados_manuales):
        """Obtener datos para la pestaña de cursos"""
        from course.models import Course
        from django.db.models import Count, Max
        
        # Obtener todos los cursos
        cursos_query = Course.objects.all()
        
        # Obtener cursos que tienen certificados (sittings aprobados)
        # CORREGIDO: Solo contar certificados únicos por curso
        cursos_con_certificados = []
        certificados_por_curso = {}
        
        for curso in cursos_query:
            certificados_curso_unicos = set()
            for s in sittings_aprobados:
                if s.quiz.course == curso and s.fecha_aprobacion:
                    clave_unica = f"{s.user.id}_{s.quiz.id}"
                    certificados_curso_unicos.add(clave_unica)
            
            if certificados_curso_unicos:
                cursos_con_certificados.append(curso)
                certificados_por_curso[curso.id] = len(certificados_curso_unicos)
        
        # Estadísticas generales de cursos
        total_cursos = len(cursos_con_certificados)
        
        # Total de estudiantes certificados (únicos)
        usuarios_unicos = set()
        for s in sittings_aprobados:
            if s.fecha_aprobacion:
                usuarios_unicos.add(s.user)
        total_estudiantes_certificados = len(usuarios_unicos)
        
        # Promedio de certificados por curso
        promedio_certificados_por_curso = 0
        if total_cursos > 0:
            total_certificados = sum(certificados_por_curso.values())
            promedio_certificados_por_curso = round(total_certificados / total_cursos, 1)
        
        # Curso más popular
        curso_mas_popular = "N/A"
        max_certificados_curso = 0
        if cursos_con_certificados:
            curso_mas_certificados = None
            max_certificados = 0
            for curso in cursos_con_certificados:
                certificados_count = certificados_por_curso.get(curso.id, 0)
                if certificados_count > max_certificados:
                    max_certificados = certificados_count
                    curso_mas_certificados = curso
            
            if curso_mas_certificados:
                curso_mas_popular = curso_mas_certificados.title
                max_certificados_curso = max_certificados
        
        # Detalle de cursos
        cursos_detalle = []
        for curso in cursos_con_certificados:
            certificados_curso = [s for s in sittings_aprobados if s.quiz.course == curso]
            ultimo_certificado = max(certificados_curso, key=lambda x: x.end) if certificados_curso else None
            
            # Obtener el instructor del curso
            instructor_curso = None
            try:
                allocation = curso.allocated_course.first()
                if allocation:
                    instructor_curso = allocation.lecturer
            except:
                instructor_curso = None
            
            cursos_detalle.append({
                'id': curso.id,
                'title': curso.title,
                'instructor': instructor_curso,
                'total_certificados': len(certificados_curso),
                'ultimo_certificado': ultimo_certificado.end if ultimo_certificado else None
            })
        
        # Ordenar por total de certificados
        cursos_detalle.sort(key=lambda x: x['total_certificados'], reverse=True)
        cursos_detalle = cursos_detalle[:20]
        
        # Datos para gráficos
        top_cursos = cursos_detalle[:10]
        cursos_labels = [curso['title'][:20] + '...' if len(curso['title']) > 20 else curso['title'] for curso in top_cursos]
        cursos_data = [curso['total_certificados'] for curso in top_cursos]
        
        # Datos de instructores
        instructores_stats = {}
        for curso in cursos_con_certificados:
            # Obtener el instructor del curso
            instructor = None
            try:
                allocation = curso.allocated_course.first()
                if allocation:
                    instructor = allocation.lecturer
            except:
                instructor = None
            
            if instructor:
                nombre = f"{instructor.first_name} {instructor.last_name}".strip()
                if not nombre or nombre == " ":
                    nombre = instructor.username
            else:
                nombre = "Sin instructor"
            
            if nombre not in instructores_stats:
                instructores_stats[nombre] = 0
            
            certificados_count = len([s for s in sittings_aprobados if s.quiz.course == curso])
            instructores_stats[nombre] += certificados_count
        
        # Ordenar instructores por total de certificados
        instructores_ordenados = sorted(instructores_stats.items(), key=lambda x: x[1], reverse=True)[:5]
        instructores_labels = [instructor[0] for instructor in instructores_ordenados]
        instructores_data_values = [instructor[1] for instructor in instructores_ordenados]
        
        return {
            'total_cursos': total_cursos,
            'total_estudiantes_certificados': total_estudiantes_certificados,
            'promedio_certificados_por_curso': promedio_certificados_por_curso,
            'curso_mas_popular': curso_mas_popular,
            'max_certificados_curso': max_certificados_curso,
            'cursos_detalle': cursos_detalle,
            'cursos_labels': cursos_labels,
            'cursos_data': cursos_data,
            'instructores_labels': instructores_labels,
            'instructores_data': instructores_data_values,
        }


@method_decorator([login_required, lecturer_required], name="dispatch")
class BeneficiariosAjaxView(View):
    """Vista AJAX para obtener datos de beneficiarios con paginación"""
    
    def get(self, request):
        try:
            from django.core.paginator import Paginator
            from django.http import JsonResponse
            
            # Obtener parámetros de paginación
            page = request.GET.get('page', 1)
            per_page = 15
            
            # Sin filtrado por instructor - mostrar todos los certificados
            
            # Obtener sittings aprobados (certificados automáticos) - OPTIMIZADO CON ORM
            from django.db.models import F
            
            # Obtener sittings completados con información del quiz
            sittings_completados = Sitting.objects.filter(
                complete=True
            ).select_related('user', 'quiz__course')
            
            # Filtrar aprobados usando Python (ya que get_max_score es un método)
            sittings_aprobados = []
            for sitting in sittings_completados:
                if sitting.get_percent_correct >= sitting.quiz.pass_mark:
                    sittings_aprobados.append(sitting)
            
            # Obtener certificados manuales
            certificados_manuales = ManualCertificate.objects.all().select_related('curso', 'generado_por')
            
            # Agrupar por usuario/beneficiario
            beneficiarios_data = {}
            
            # Procesar certificados automáticos (participantes)
            for sitting in sittings_aprobados:
                user_id = sitting.user.id
                if user_id not in beneficiarios_data:
                    beneficiarios_data[user_id] = {
                        'id': user_id,
                        'nombre': f"{sitting.user.first_name} {sitting.user.last_name}".strip() or sitting.user.username,
                        'email': sitting.user.email,
                        'tipo': 'Participante',
                        'total_certificados': 0,
                        'automaticos': 0,
                        'manuales': 0,
                        'ultimo_certificado': None,
                        'fecha_comparacion': None
                    }
                
                beneficiarios_data[user_id]['automaticos'] += 1
                beneficiarios_data[user_id]['total_certificados'] += 1
                
                # Actualizar último certificado
                if sitting.end:
                    fecha_sitting = sitting.end.strftime('%d/%m/%Y')
                    if not beneficiarios_data[user_id]['ultimo_certificado'] or sitting.end > beneficiarios_data[user_id]['fecha_comparacion']:
                        beneficiarios_data[user_id]['ultimo_certificado'] = fecha_sitting
                        beneficiarios_data[user_id]['fecha_comparacion'] = sitting.end
            
            # Procesar certificados manuales (incluyendo no participantes)
            for cert in certificados_manuales:
                # Usar el nombre del certificado manual como identificador único
                nombre_cert = cert.nombre_completo or f"{cert.generado_por.first_name} {cert.generado_por.last_name}".strip() or cert.generado_por.username
                cert_id = f"manual_{cert.id}"  # ID único para certificados manuales
                
                if cert_id not in beneficiarios_data:
                    beneficiarios_data[cert_id] = {
                        'id': cert_id,
                        'nombre': nombre_cert,
                        'email': cert.generado_por.email or 'No disponible',
                        'tipo': 'Certificado Manual',
                        'total_certificados': 0,
                        'automaticos': 0,
                        'manuales': 0,
                        'ultimo_certificado': None,
                        'fecha_comparacion': None
                    }
                
                beneficiarios_data[cert_id]['manuales'] += 1
                beneficiarios_data[cert_id]['total_certificados'] += 1
                
                # Actualizar último certificado
                if cert.fecha_generacion:
                    fecha_str = cert.fecha_generacion.strftime('%d/%m/%Y')
                    if not beneficiarios_data[cert_id]['ultimo_certificado'] or cert.fecha_generacion > beneficiarios_data[cert_id]['fecha_comparacion']:
                        beneficiarios_data[cert_id]['ultimo_certificado'] = fecha_str
                        beneficiarios_data[cert_id]['fecha_comparacion'] = cert.fecha_generacion
            
            # Convertir a lista y ordenar por total de certificados
            beneficiarios = list(beneficiarios_data.values())
            beneficiarios.sort(key=lambda x: x['total_certificados'], reverse=True)
            
            # Limpiar datos antes de enviar (remover campo temporal)
            for beneficiario in beneficiarios:
                if 'fecha_comparacion' in beneficiario:
                    del beneficiario['fecha_comparacion']
            
            # Aplicar paginación
            paginator = Paginator(beneficiarios, per_page)
            page_obj = paginator.get_page(page)
            
            return JsonResponse({
                'success': True,
                'beneficiarios': list(page_obj),
                'pagination': {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'total_items': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                    'per_page': per_page
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al obtener beneficiarios: {str(e)}'
            })

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
            
            # Sin filtrado por instructor - mostrar todos los certificados
            
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
                # Certificados automáticos del curso - OPTIMIZADO CON ORM
                from django.db.models import F
                
                # Obtener sittings completados del curso con información del quiz
                sittings_completados = Sitting.objects.filter(
                    complete=True,
                    quiz__course=curso
                ).select_related('quiz', 'user')
                
                # Filtrar aprobados usando Python (ya que get_max_score es un método)
                sittings_aprobados = []
                for sitting in sittings_completados:
                    if sitting.get_percent_correct >= sitting.quiz.pass_mark:
                        sittings_aprobados.append(sitting)
                
                # Certificados manuales del curso
                certificados_manuales = ManualCertificate.objects.filter(curso=curso)
                
                # Calcular estadísticas
                total_automaticos = len(sittings_aprobados)
                total_manuales = certificados_manuales.count()
                total_curso = total_automaticos + total_manuales
                
                # Importar funciones unificadas
                from .certificate_utils import (
                    is_certificate_active, 
                    is_certificate_expired
                )
                
                # Certificados activos (no vencidos) - LÓGICA UNIFICADA
                automaticos_activos = len([s for s in sittings_aprobados if is_certificate_active(s, hoy)])
                manuales_activos = len([c for c in certificados_manuales if is_certificate_active(c, hoy)])
                total_activos = automaticos_activos + manuales_activos
                
                # Certificados vencidos - LÓGICA UNIFICADA
                automaticos_vencidos = len([s for s in sittings_aprobados if is_certificate_expired(s, hoy)])
                manuales_vencidos = len([c for c in certificados_manuales if is_certificate_expired(c, hoy)])
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

@method_decorator([login_required, admin_required], name="dispatch")
class SittingDateUpdateView(UpdateView):
    """Vista para editar fecha_aprobacion de forma completamente libre"""
    model = Sitting
    form_class = SittingDateUpdateForm
    template_name = 'quiz/update_sitting_date.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sitting'] = self.object
        context['audit_logs'] = SittingAuditLog.objects.filter(
            sitting=self.object
        ).order_by('-changed_at')[:10]
        return context
    
    def form_valid(self, form):
        new_date = form.cleaned_data['fecha_aprobacion']
        reason = self.request.POST.get('reason', '')
        
        try:
            self.object.update_approval_date_freely(
                new_date, 
                self.request.user, 
                reason,
                self.request
            )
            messages.success(self.request, "Fecha de aprobación actualizada correctamente")
            return redirect('quiz_marking')
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)


@method_decorator([login_required, lecturer_required], name="dispatch")
class CertificadosFiltrosAjaxView(View):
    """Vista AJAX para aplicar filtros reales a los datos de certificados"""
    
    def post(self, request, *args, **kwargs):
        from django.http import JsonResponse
        from course.models import Course
        from datetime import date, timedelta, datetime
        import json
        
        try:
            # Obtener parámetros de filtro
            filtros = json.loads(request.body)
            
            # Sin filtrado por instructor - mostrar todos los certificados
            
            # Obtener datos base
            hoy = date.today()
            en_30_dias = hoy + timedelta(days=30)
            
            # Función helper para convertir datetime a date
            def datetime_to_date(dt):
                if dt is None:
                    return None
                if isinstance(dt, datetime):
                    return dt.date()
                return dt
            
            # Obtener certificados automáticos (aprobados) - OPTIMIZADO CON ORM
            from django.db.models import F
            
            # Obtener sittings completados con información del quiz
            sittings_completados = Sitting.objects.filter(
                complete=True
            ).select_related('quiz', 'course', 'user')
            
            # Filtrar aprobados usando Python (ya que get_max_score es un método)
            sittings_aprobados = []
            for sitting in sittings_completados:
                if sitting.get_percent_correct >= sitting.quiz.pass_mark:
                    sittings_aprobados.append(sitting)
            
            # Obtener certificados manuales
            certificados_manuales = ManualCertificate.objects.all()
            
            # APLICAR FILTROS REALES
            
            # Filtro por tipo
            if filtros.get('tipo') == 'automaticos':
                certificados_manuales = ManualCertificate.objects.none()
            elif filtros.get('tipo') == 'manuales':
                sittings_aprobados = []
            
            # Filtro por fechas
            if filtros.get('fechaDesde') and filtros.get('fechaHasta'):
                fecha_desde = datetime.strptime(filtros['fechaDesde'], '%Y-%m-%d').date()
                fecha_hasta = datetime.strptime(filtros['fechaHasta'], '%Y-%m-%d').date()
                
                # Filtrar automáticos por fecha de finalización
                sittings_aprobados = [s for s in sittings_aprobados 
                                   if s.end and fecha_desde <= datetime_to_date(s.end) <= fecha_hasta]
                
                # Filtrar manuales por fecha de generación
                certificados_manuales = certificados_manuales.filter(
                    fecha_generacion__date__range=[fecha_desde, fecha_hasta]
                )
            
            # Filtro por cursos
            if filtros.get('cursos') and len(filtros['cursos']) > 0:
                curso_ids = [int(cid) for cid in filtros['cursos']]
                
                # Filtrar automáticos por curso
                sittings_aprobados = [s for s in sittings_aprobados 
                                   if s.course.id in curso_ids]
                
                # Filtrar manuales por curso
                certificados_manuales = certificados_manuales.filter(curso_id__in=curso_ids)
            
            # Calcular estadísticas filtradas
            total_automaticos = len(sittings_aprobados)
            total_manuales = certificados_manuales.count()
            total_certificados = total_automaticos + total_manuales
            
            # Importar funciones unificadas
            from .certificate_utils import (
                is_certificate_active, 
                is_certificate_expired, 
                is_certificate_expiring_soon
            )
            
            # Calcular activos y vencidos - LÓGICA UNIFICADA
            automaticos_activos = len([s for s in sittings_aprobados if is_certificate_active(s, hoy)])
            manuales_activos = len([c for c in certificados_manuales if is_certificate_active(c, hoy)])
            certificados_activos = automaticos_activos + manuales_activos
            
            automaticos_vencidos = len([s for s in sittings_aprobados if is_certificate_expired(s, hoy)])
            manuales_vencidos = len([c for c in certificados_manuales if is_certificate_expired(c, hoy)])
            certificados_vencidos = automaticos_vencidos + manuales_vencidos
            
            # Calcular por vencer - LÓGICA UNIFICADA
            automaticos_por_vencer = len([s for s in sittings_aprobados if is_certificate_expiring_soon(s, hoy, 30)])
            manuales_por_vencer = len([c for c in certificados_manuales if is_certificate_expiring_soon(c, hoy, 30)])
            por_vencer = automaticos_por_vencer + manuales_por_vencer
            
            # Generar datos mensuales filtrados
            datos_mensuales = self.generar_datos_mensuales_filtrados(
                sittings_aprobados, certificados_manuales
            )
            
            return JsonResponse({
                'success': True,
                'data': {
                    'total_certificados': total_certificados,
                    'total_automaticos': total_automaticos,
                    'total_manuales': total_manuales,
                    'certificados_activos': certificados_activos,
                    'certificados_vencidos': certificados_vencidos,
                    'por_vencer': por_vencer,
                    'automaticos_activos': automaticos_activos,
                    'manuales_activos': manuales_activos,
                    'automaticos_vencidos': automaticos_vencidos,
                    'manuales_vencidos': manuales_vencidos,
                    'datos_mensuales': datos_mensuales
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al aplicar filtros: {str(e)}'
            })
    
    def generar_datos_mensuales_filtrados(self, sittings_aprobados, certificados_manuales):
        """Generar datos mensuales con filtros aplicados"""
        from datetime import date, timedelta
        
        datos = []
        for i in range(12):
            fecha = date.today() - timedelta(days=30*i)
            inicio_mes = fecha.replace(day=1)
            fin_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            # Certificados automáticos del mes
            automaticos = 0
            for sitting in sittings_aprobados:
                if sitting.end:
                    sitting_date = sitting.end.date() if hasattr(sitting.end, 'date') else sitting.end
                    if inicio_mes <= sitting_date <= fin_mes:
                        automaticos += 1
            
            # Certificados manuales del mes
            manuales = 0
            for cert in certificados_manuales:
                if cert.fecha_generacion:
                    cert_date = cert.fecha_generacion.date() if hasattr(cert.fecha_generacion, 'date') else cert.fecha_generacion
                    if inicio_mes <= cert_date <= fin_mes:
                        manuales += 1
            
            datos.append({
                'mes': fecha.strftime('%b %Y'),
                'automaticos': automaticos,
                'manuales': manuales,
                'total': automaticos + manuales
            })
        
        return list(reversed(datos))
