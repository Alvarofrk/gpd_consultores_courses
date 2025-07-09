from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django import forms
from django.db import transaction
from django.http import HttpResponse, HttpResponseNotAllowed, FileResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from io import BytesIO
from datetime import datetime
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import io
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Q
from django.conf import settings
import os
import json
import calendar
import qrcode
from PIL import Image, ImageDraw, ImageFont
import base64
from decimal import Decimal
import math

from accounts.decorators import admin_required, lecturer_required
from accounts.models import User, Student
from .forms import SessionForm, SemesterForm, NewsAndEventsForm, CotizacionForm, ItemCotizacionFormSet, EventoForm, FiltroEventoForm
from .models import NewsAndEvents, ActivityLog, Session, Semester, Cotizacion, ItemCotizacion, HistorialEstado, Evento, LogRecordatorio


def generate_qr_code(data, size=150, format='PNG'):
    """
    Genera un código QR a partir de datos (URL o texto)
    
    Args:
        data (str): Los datos a codificar en el QR
        size (int): Tamaño del código QR en píxeles
        format (str): Formato de salida ('PNG', 'JPEG', 'PDF')
    
    Returns:
        PIL.Image: Imagen del código QR
    """
    try:
        # Crear el código QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # Crear la imagen
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Redimensionar si es necesario
        if size != 150:
            try:
                # Para versiones más nuevas de PIL
                qr_image = qr_image.resize((size, size), Image.Resampling.LANCZOS)
            except AttributeError:
                try:
                    # Para versiones más antiguas de PIL
                    qr_image = qr_image.resize((size, size), Image.LANCZOS)
                except AttributeError:
                    # Fallback para versiones muy antiguas
                    qr_image = qr_image.resize((size, size))
        
        return qr_image
    except Exception as e:
        print(f"ERROR en generate_qr_code: {e}")
        # En caso de error, crear un QR básico
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Redimensionar si es necesario
        if size != 150:
            try:
                qr_image = qr_image.resize((size, size), Image.Resampling.LANCZOS)
            except AttributeError:
                try:
                    qr_image = qr_image.resize((size, size), Image.LANCZOS)
                except AttributeError:
                    qr_image = qr_image.resize((size, size))
        
        return qr_image


# ########################################################
# News & Events
# ########################################################
@login_required
def home_view(request):
    items = NewsAndEvents.objects.all().order_by("-updated_date")
    context = {
        "title": "News & Events",
        "items": items,
    }
    return render(request, "core/index.html", context)


@login_required
@admin_required
def dashboard_view(request):
    logs = ActivityLog.objects.all().order_by("-created_at")[:10]
    gender_count = Student.get_gender_count()
    context = {
        "student_count": User.objects.get_student_count(),
        "lecturer_count": User.objects.get_lecturer_count(),
        "superuser_count": User.objects.get_superuser_count(),
        "males_count": gender_count["M"],
        "females_count": gender_count["F"],
        "logs": logs,
    }
    return render(request, "core/dashboard.html", context)


@login_required
def post_add(request):
    if request.method == "POST":
        form = NewsAndEventsForm(request.POST)
        title = form.cleaned_data.get("title", "Post") if form.is_valid() else None
        if form.is_valid():
            form.save()
            messages.success(request, f"{title} has been uploaded.")
            return redirect("home")
        messages.error(request, "Please correct the error(s) below.")
    else:
        form = NewsAndEventsForm()
    return render(request, "core/post_add.html", {"title": "Add Post", "form": form})


@login_required
@lecturer_required
def edit_post(request, pk):
    instance = get_object_or_404(NewsAndEvents, pk=pk)
    if request.method == "POST":
        form = NewsAndEventsForm(request.POST, instance=instance)
        title = form.cleaned_data.get("title", "Post") if form.is_valid() else None
        if form.is_valid():
            form.save()
            messages.success(request, f"{title} has been updated.")
            return redirect("home")
        messages.error(request, "Please correct the error(s) below.")
    else:
        form = NewsAndEventsForm(instance=instance)
    return render(request, "core/post_add.html", {"title": "Edit Post", "form": form})


@login_required
@lecturer_required
def delete_post(request, pk):
    post = get_object_or_404(NewsAndEvents, pk=pk)
    post_title = post.title
    post.delete()
    messages.success(request, f"{post_title} has been deleted.")
    return redirect("home")


# ########################################################
# Session
# ########################################################
@login_required
@lecturer_required
def session_list_view(request):
    """Show list of all sessions"""
    sessions = Session.objects.all().order_by("-is_current_session", "-session")
    return render(request, "core/session_list.html", {"sessions": sessions})


@login_required
@lecturer_required
def session_add_view(request):
    """Add a new session"""
    if request.method == "POST":
        form = SessionForm(request.POST)
        if form.is_valid():
            if form.cleaned_data.get("is_current_session"):
                unset_current_session()
            form.save()
            messages.success(request, "Session added successfully.")
            return redirect("session_list")
    else:
        form = SessionForm()
    return render(request, "core/session_update.html", {"form": form})


@login_required
@lecturer_required
def session_update_view(request, pk):
    session = get_object_or_404(Session, pk=pk)
    if request.method == "POST":
        form = SessionForm(request.POST, instance=session)
        if form.is_valid():
            if form.cleaned_data.get("is_current_session"):
                unset_current_session()
            form.save()
            messages.success(request, "Session updated successfully.")
            return redirect("session_list")
    else:
        form = SessionForm(instance=session)
    return render(request, "core/session_update.html", {"form": form})


@login_required
@lecturer_required
def session_delete_view(request, pk):
    session = get_object_or_404(Session, pk=pk)
    if session.is_current_session:
        messages.error(request, "You cannot delete the current session.")
    else:
        session.delete()
        messages.success(request, "Session successfully deleted.")
    return redirect("session_list")


def unset_current_session():
    """Unset current session"""
    current_session = Session.objects.filter(is_current_session=True).first()
    if current_session:
        current_session.is_current_session = False
        current_session.save()


# ########################################################
# Semester
# ########################################################
@login_required
@lecturer_required
def semester_list_view(request):
    semesters = Semester.objects.all().order_by("-is_current_semester", "-semester")
    return render(request, "core/semester_list.html", {"semesters": semesters})


@login_required
@lecturer_required
def semester_add_view(request):
    if request.method == "POST":
        form = SemesterForm(request.POST)
        if form.is_valid():
            if form.cleaned_data.get("is_current_semester"):
                unset_current_semester()
                unset_current_session()
            form.save()
            messages.success(request, "Semester added successfully.")
            return redirect("semester_list")
    else:
        form = SemesterForm()
    return render(request, "core/semester_update.html", {"form": form})


@login_required
@lecturer_required
def semester_update_view(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    if request.method == "POST":
        form = SemesterForm(request.POST, instance=semester)
        if form.is_valid():
            if form.cleaned_data.get("is_current_semester"):
                unset_current_semester()
                unset_current_session()
            form.save()
            messages.success(request, "Semester updated successfully!")
            return redirect("semester_list")
    else:
        form = SemesterForm(instance=semester)
    return render(request, "core/semester_update.html", {"form": form})


@login_required
@lecturer_required
def semester_delete_view(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    if semester.is_current_semester:
        messages.error(request, "You cannot delete the current semester.")
    else:
        semester.delete()
        messages.success(request, "Semester successfully deleted.")
    return redirect("semester_list")


def unset_current_semester():
    """Unset current semester"""
    current_semester = Semester.objects.filter(is_current_semester=True).first()
    if current_semester:
        current_semester.is_current_semester = False
        current_semester.save()


@login_required
def cotizaciones_list_view(request):
    """Lista de cotizaciones con filtros y paginación"""
    cotizaciones = Cotizacion.objects.all().order_by('-cotizacion')
    
    # Filtros
    estado = request.GET.get('estado')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    cliente = request.GET.get('cliente')
    
    if estado:
        cotizaciones = cotizaciones.filter(estado=estado)
    if fecha_desde:
        cotizaciones = cotizaciones.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        cotizaciones = cotizaciones.filter(fecha__lte=fecha_hasta)
    if cliente:
        cotizaciones = cotizaciones.filter(cliente__icontains=cliente)
    
    # Paginación
    paginator = Paginator(cotizaciones, 10)  # 10 items por página
    page = request.GET.get('page')
    try:
        cotizaciones = paginator.page(page)
    except PageNotAnInteger:
        cotizaciones = paginator.page(1)
    except EmptyPage:
        cotizaciones = paginator.page(paginator.num_pages)
    
    context = {
        'cotizaciones': cotizaciones,
        'estados': Cotizacion.ESTADO_CHOICES,
        'estado_actual': estado,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'cliente': cliente,
    }
    return render(request, 'core/cotizaciones_list.html', context)


@login_required
def cotizacion_add_view(request):
    if request.method == 'POST':
        form = CotizacionForm(request.POST)
        formset = ItemCotizacionFormSet(request.POST, prefix='items')
        if form.is_valid():
            try:
                with transaction.atomic():
                    cotizacion = form.save(commit=False)
                    formset = ItemCotizacionFormSet(request.POST, instance=cotizacion, prefix='items')
                    if formset.is_valid():
                        instances = formset.save(commit=False)
                        items_validos = []
                        for form_item, instance in zip(formset.forms, instances):
                            # Omitir los ítems marcados para borrar
                            if form_item.cleaned_data.get('DELETE'):
                                continue
                            if instance.curso or instance.descripcion or instance.duracion or instance.cantidad or instance.precio_unitario:
                                instance.cotizacion = cotizacion
                                items_validos.append(instance)
                        if not items_validos:
                            messages.error(request, "Debe agregar al menos un ítem a la cotización.")
                            return render(request, 'core/cotizacion_form.html', {
                                'form': form,
                                'formset': formset,
                                'title': 'Nueva Cotización'
                            })
                        cotizacion.creado_por = request.user
                        cotizacion.save()
                        for instance in items_validos:
                            instance.save()
                        total = sum(item.subtotal for item in cotizacion.items.all())
                        cotizacion.monto_total = total
                        cotizacion.save()
                        messages.success(request, "Cotización creada exitosamente.")
                        return redirect('cotizaciones_list')
                    else:
                        for i, error in enumerate(formset.errors):
                            if error and not formset.forms[i].cleaned_data.get('DELETE'):
                                messages.error(request, f"Error en item: {error}")
                        for error in formset.non_form_errors():
                            messages.error(request, error)
            except Exception as e:
                messages.error(request, f"Error al crear la cotización: {str(e)}")
        else:
            messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = CotizacionForm(initial={'estado': 'pendiente'})
        formset = ItemCotizacionFormSet(prefix='items')
    return render(request, 'core/cotizacion_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Nueva Cotización'
    })


@login_required
def cotizacion_detail_view(request, pk):
    """Ver detalles de una cotización"""
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    
    # Verificar permisos
    if not request.user.is_superuser and cotizacion.creado_por != request.user:
        messages.error(request, "No tienes permiso para ver esta cotización.")
        return redirect("cotizaciones_list")
    
    return render(request, "core/cotizacion_detail.html", {"cotizacion": cotizacion})


@login_required
def cotizacion_update_view(request, pk):
    """Actualizar una cotización existente"""
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    # Verificar permisos
    if not request.user.is_superuser and cotizacion.creado_por != request.user:
        messages.error(request, "No tienes permiso para editar esta cotización.")
        return redirect("cotizaciones_list")
    if request.method == "POST":
        form = CotizacionForm(request.POST, instance=cotizacion)
        formset = ItemCotizacionFormSet(request.POST, instance=cotizacion, prefix='items')
        if form.is_valid():
            if formset.is_valid():
                try:
                    with transaction.atomic():
                        if not request.user.is_superuser:
                            form.instance.estado = cotizacion.estado
                        cotizacion = form.save()
                        instances = formset.save(commit=False)
                        # Eliminar items marcados para eliminación
                        for obj in formset.deleted_objects:
                            obj.delete()
                        # Guardar solo los ítems con datos relevantes y no marcados para borrar
                        for form_item, instance in zip(formset.forms, instances):
                            if form_item.cleaned_data.get('DELETE'):
                                continue
                            if instance.curso or instance.descripcion or instance.duracion or instance.cantidad or instance.precio_unitario:
                                instance.cotizacion = cotizacion
                                instance.save()
                        # Recalcular el monto total
                        total = sum(item.subtotal for item in cotizacion.items.all())
                        cotizacion.monto_total = total
                        cotizacion.save()
                        messages.success(request, "Cotización actualizada exitosamente.")
                        return redirect("cotizaciones_list")
                except Exception as e:
                    messages.error(request, f"Error al guardar la cotización: {str(e)}")
            else:
                for i, error in enumerate(formset.errors):
                    if error and not formset.forms[i].cleaned_data.get('DELETE'):
                        messages.error(request, f"Error en item: {error}")
                for error in formset.non_form_errors():
                    messages.error(request, error)
        else:
            messages.error(request, "Por favor corrija los errores en el formulario principal.")
    else:
        form = CotizacionForm(instance=cotizacion)
        if not request.user.is_superuser:
            form.fields['estado'].widget = forms.HiddenInput()
        formset = ItemCotizacionFormSet(instance=cotizacion, prefix='items')
    return render(request, "core/cotizacion_form.html", {
        "form": form,
        "formset": formset,
        "title": "Editar Cotización",
        "cotizacion": cotizacion
    })


@login_required
def cotizacion_delete_view(request, pk):
    """Eliminar una cotización"""
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    
    # Verificar permisos
    if not request.user.is_superuser and cotizacion.creado_por != request.user:
        messages.error(request, "No tienes permiso para eliminar esta cotización.")
        return redirect("cotizaciones_list")
    
    if request.method == "POST":
        cotizacion.delete()
        messages.success(request, "Cotización eliminada exitosamente.")
        return redirect("cotizaciones_list")
    
    return render(request, "core/cotizacion_confirm_delete.html", {"cotizacion": cotizacion})


@login_required
def cotizacion_change_status_view(request, pk):
    """Cambiar el estado de una cotización"""
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])
    
    if not request.user.is_superuser:
        messages.error(request, "Solo los administradores pueden cambiar el estado de las cotizaciones.")
        return redirect("cotizaciones_list")
    
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    nuevo_estado = request.POST.get("estado")
    comentario = request.POST.get("comentario", "")
    
    if nuevo_estado in dict(Cotizacion.ESTADO_CHOICES):
        try:
            with transaction.atomic():
                # Crear registro en el historial
                HistorialEstado.objects.create(
                    cotizacion=cotizacion,
                    estado_anterior=cotizacion.estado,
                    estado_nuevo=nuevo_estado,
                    usuario=request.user,
                    comentario=comentario
                )
                
                # Actualizar estado
                cotizacion.estado = nuevo_estado
                cotizacion.save()
                
                messages.success(request, f"Estado de la cotización cambiado a {cotizacion.get_estado_display()}.")
        except Exception as e:
            messages.error(request, f"Error al cambiar el estado: {str(e)}")
    else:
        messages.error(request, "Estado no válido.")
    
    return redirect("cotizaciones_list")


@login_required
def cotizacion_download_pdf(request, pk):
    """Generar y descargar PDF de la cotización con flowables y paginación automática"""
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    import os
    from decimal import Decimal
    import math
    from reportlab.platypus import KeepTogether

    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=30, rightMargin=30, topMargin=10, bottomMargin=5)
    width, height = letter
    elements = []
    styles = getSampleStyleSheet()

    # --- 1. Encabezado: Logos y título ---
    logo1_path = os.path.join('static', 'img', 'logo1.jpg')
    iso_path = os.path.join('static', 'img', 'iso.PNG')
    logo1 = None
    iso = None
    if os.path.exists(logo1_path):
        logo1 = Image(logo1_path, width=2.0*inch, height=1.0*inch)
    if os.path.exists(iso_path):
        iso = Image(iso_path, width=1.0*inch, height=0.9*inch)
    logo_table_data = [[logo1 if logo1 else '', '', iso if iso else '']]
    logo_table = Table(logo_table_data, colWidths=[2.2*inch, width-3.7*inch, 1.2*inch])
    logo_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 10),
        ('RIGHTPADDING', (2, 0), (2, 0), 10),
        ('LEFTPADDING', (1, 0), (1, 0), 0),
        ('RIGHTPADDING', (1, 0), (1, 0), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(logo_table)
    # Quitar el Spacer aquí para que el título quede pegado a los logos
    # elements.append(Spacer(1, 2))

    # Título y datos empresa
    title_style = ParagraphStyle('title', parent=styles['Heading2'], alignment=1, fontSize=12, fontName='Helvetica-Bold')
    elements.append(Paragraph('“AÑO DE LA RECUPERACIÓN Y CONSOLIDACIÓN DE LA ECONOMÍA PERUANA”', title_style))
    info_style = ParagraphStyle('info', parent=styles['Normal'], fontSize=8, leading=10)
    empresa_info = (
        'Residencial los Álamos Mz. A5 piso Nº 3 – Cerro Colorado<br/>'
        'RUC: 20604885141<br/>'
        '944 065 297 – 991 087 490<br/>'
        'ventas@gpdconsultoressac.com'
    )
    elaborado_aprobado = (
        '<b>Elaborado por:</b> Área Comercial<br/><b>Aprobado por:</b> Gerente General'
    )
    info_table = Table([
        [Paragraph(empresa_info, info_style), Paragraph(elaborado_aprobado, ParagraphStyle('right', parent=info_style, alignment=2))]
    ], colWidths=[width*0.55, width*0.45])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('LEFTPADDING', (0,0), (0,0), 40),
        ('RIGHTPADDING', (1,0), (1,0), 40),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(info_table)
    elements.append(Table([[" "]], colWidths=[width-60], rowHeights=[2], style=TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1a3764'))])))
    elements.append(Spacer(1, 1))

    # --- 2. Datos de cliente y cotización ---
    datos_cliente = [
        [Paragraph('<b>Dirigido a:</b>', info_style), cotizacion.dirigido_a or '-', '', Paragraph('<b>Cotización:</b>', info_style), cotizacion.cotizacion or '-'],
        [Paragraph('<b>Empresa:</b>', info_style), cotizacion.empresa or '-', '', Paragraph('<b>Tipo de Cotización:</b>', info_style), cotizacion.tipo_cotizacion or '-'],
        [Paragraph('<b>RUC:</b>', info_style), cotizacion.ruc or '-', '', Paragraph('<b>Fecha de Cotización:</b>', info_style), cotizacion.fecha_cotizacion.strftime('%d/%m/%Y') if cotizacion.fecha_cotizacion else '-'],
        ['', '', '', Paragraph('<b>Validez de la Cotización:</b>', info_style), cotizacion.validez_cotizacion.strftime('%d/%m/%Y') if cotizacion.validez_cotizacion else '-'],
    ]
    table_cliente = Table(datos_cliente, colWidths=[60, 240, 0, 110, 120])
    table_cliente.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(table_cliente)
    elements.append(Spacer(1, 8))
    elements.append(Table([[" "]], colWidths=[width-60], rowHeights=[2], style=TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.orange)])))

    # --- 3. Servicio y detalles ---
    servicio_style = ParagraphStyle('servicio', parent=info_style, fontSize=7, leading=8)
    elements.append(Paragraph('<b>Servicio:</b>', info_style))
    servicio_texto = (cotizacion.servicio or '-').replace('\n', '<br/>')
    elements.append(Paragraph(servicio_texto, servicio_style))
    elements.append(Spacer(1, 4))
    detalles = [
        [Paragraph('<b>Modalidad:</b>', info_style), cotizacion.get_modalidad_display() or '-'],
        [Paragraph('<b>Sede del servicio:</b>', info_style), cotizacion.sede_servicio or '-'],
        [Paragraph('<b>Fecha del servicio:</b>', info_style), cotizacion.fecha_servicio.strftime('%d/%m/%Y') if cotizacion.fecha_servicio else '-'],
    ]
    table_detalles = Table(detalles, colWidths=[80, 350])
    table_detalles.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(table_detalles)
    elements.append(Spacer(1, 8))

    # --- 4. Tabla de ítems ---
    styleN = ParagraphStyle('tabla', parent=info_style, fontSize=8, leading=10)
    styleHeader = ParagraphStyle('tablaHeader', parent=styleN, textColor=colors.white, fontName='Helvetica-Bold')
    items_data = [[
        Paragraph('<b>Descripción</b>', styleHeader), Paragraph('<b>Curso</b>', styleHeader), Paragraph('<b>Duración (Horas Certificado)</b>', styleHeader),
        Paragraph('<b>Precio Unit.</b>', styleHeader), Paragraph('<b>Cantidad</b>', styleHeader), Paragraph('<b>Inversión S/.</b>', styleHeader)
    ]]
    for item in cotizacion.items.all():
        desc = Paragraph(item.descripcion or '-', styleN)
        curso = Paragraph(item.curso or '-', styleN)
        items_data.append([
            desc,
            curso,
            item.duracion or '-',
            f"S/ {item.precio_unitario:.2f}",
            str(item.cantidad),
            f"S/ {item.subtotal:.2f}"
        ])
    table_items = Table(items_data, colWidths=[170, 120, 55, 60, 50, 80], repeatRows=1)
    table_items.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a3764')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 7),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(table_items)
    elements.append(Spacer(1, 10))

    # --- 5. Totales ---
    totales_data = [
        [Paragraph('<b>TOTAL, S/:</b>', info_style), f"S/ {math.ceil(float(cotizacion.total_con_igv) * 10) / 10:.2f}"],
        [Paragraph('<b>SUBTOTAL</b>', info_style), f"S/ {cotizacion.monto_total:.2f}"],
        [Paragraph('<b>IGV</b>', info_style), f"S/ {math.ceil(float(cotizacion.igv) * 10) / 10:.2f}"],
        [Paragraph('<b>INVERSIÓN TOTAL A DEPOSITAR</b>', info_style), f"S/ {math.ceil(float(cotizacion.total_con_igv) * 10) / 10:.2f}"],
    ]
    table_totales = Table(totales_data, colWidths=[200, 100], hAlign='RIGHT')
    table_totales.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(table_totales)
    elements.append(Spacer(1, 10))

    # --- 6. Medios de pago ---
    medios_pago = []
    medios_pago.append(Paragraph('<b>MEDIOS DE PAGO</b>', ParagraphStyle('medios', parent=info_style, textColor=colors.white, backColor=colors.HexColor('#1a3764'), fontSize=9, leftIndent=0, alignment=0)))
    medios_pago.append(Spacer(1, 2))
    medios_pago.append(Paragraph(f"<b>Tiempo de entrega:</b> {cotizacion.tiempo_entrega or '-'}", info_style))
    # Forma de pago
    total_final = cotizacion.total_con_detraccion
    if cotizacion.forma_pago == '50_50':
        adelanto_monto = total_final * Decimal('0.5')
        saldo_monto = total_final * Decimal('0.5')
        adelanto_pct = "50%"
        saldo_pct = "50%"
        forma_pago_texto = "50% al iniciar y 50% al finalizar"
    elif cotizacion.forma_pago == '100_adelantado':
        adelanto_monto = total_final
        saldo_monto = Decimal('0')
        adelanto_pct = "100%"
        saldo_pct = "0%"
        forma_pago_texto = "100% adelantado"
    elif cotizacion.forma_pago == 'al_credito':
        adelanto_monto = Decimal('0')
        saldo_monto = total_final
        adelanto_pct = "0%"
        saldo_pct = "100%"
        forma_pago_texto = "Al crédito"
    else:
        adelanto_monto = Decimal('0')
        saldo_monto = total_final
        adelanto_pct = "0%"
        saldo_pct = "100%"
        forma_pago_texto = "-"
    texto_pago = f"{forma_pago_texto}   |   Adelanto: {adelanto_pct} (S/ {adelanto_monto:.2f})   |   Saldo: {saldo_pct} (S/ {saldo_monto:.2f})"
    medios_pago.append(Paragraph(f"<b>Forma de pago:</b> {texto_pago}", info_style))
    # Plazo de crédito
    if cotizacion.forma_pago == 'al_credito':
        plazo_texto = ""
        if cotizacion.plazo_credito_dias:
            plazo_texto = f"Plazo: {cotizacion.plazo_credito_dias} días"
        elif cotizacion.plazo_credito_fecha:
            plazo_texto = f"Plazo: Hasta {cotizacion.plazo_credito_fecha.strftime('%d/%m/%Y')}"
        if plazo_texto:
            medios_pago.append(Paragraph(plazo_texto, info_style))
        if cotizacion.fecha_vencimiento_calculada:
            medios_pago.append(Paragraph(f"Vencimiento: {cotizacion.fecha_vencimiento_calculada.strftime('%d/%m/%Y')}", info_style))
        if cotizacion.dias_restantes_credito is not None:
            if cotizacion.dias_restantes_credito > 0:
                medios_pago.append(Paragraph(f"Días restantes: {cotizacion.dias_restantes_credito}", info_style))
            else:
                medios_pago.append(Paragraph("ESTADO: VENCIDO", info_style))
        estado_texto = ""
        if cotizacion.estado_credito == 'pagado':
            estado_texto = "ESTADO: PAGADO"
        elif cotizacion.estado_credito == 'parcial':
            estado_texto = f"ESTADO: PAGO PARCIAL ({cotizacion.porcentaje_pagado_credito:.1f}%)"
        elif cotizacion.estado_credito == 'vencido':
            estado_texto = "ESTADO: VENCIDO"
        else:
            estado_texto = "ESTADO: PENDIENTE"
        medios_pago.append(Paragraph(estado_texto, info_style))
    # Cuentas
    medios_pago.append(Paragraph("Cuenta de ahorros BCP: 215-95088021-001", info_style))
    medios_pago.append(Paragraph("Cuenta CCI: 00221519508802100123", info_style))
    medios_pago.append(Paragraph("CUENTA de detracciones Banco de la Nación-SOLES: 00-113-039019", info_style))
    medios_pago.append(Paragraph(f"12% DE DETRACCIÓN - Banco de la Nación*: S/ {math.ceil(float(cotizacion.detraccion) * 10) / 10:.2f}", info_style))
    elements.extend(medios_pago)
    elements.append(Spacer(1, 10))

    # --- 7. Consideraciones generales y firmas ---
    cons_style = ParagraphStyle('cons', parent=info_style, fontSize=7, leading=9)
    elements.append(Paragraph('<b>Consideraciones generales del servicio</b>', cons_style))
    consideraciones = [
        "1. Se tomará en cuenta la asistencia y la nota mínima de aprobación que es 14 (70%)",
        "2. G.P.D Consultores brinda: Certificado de cada curso para los participantes, material didáctico, acceso a nuestra página web.",
        "3. El servicio se brindará con un aviso mínimo de 48 horas de anticipación y previa confirmación del pago, ya sea parcial o total.",
        "4. Cambios de fecha y cancelaciones: Cualquier cambio debe notificarse 48 horas antes del curso, aplicando una penalización del 30% sobre el monto acordado.",
        "5. Confirmación de acuerdos: Todos los compromisos serán válidos únicamente si son confirmados por correo electrónico por un representante autorizado de GPD CONSULTORES.",
        "6. PRESENCIAL (mínimo 8 participantes) previa coordinación, VIRTUAL SINCRÓNICO (mínimo 7 participantes) reunión TEAMS, VIRTUAL ASINCRÓNICO (sin mínimo de participantes) clase grabada."
    ]
    for c in consideraciones:
        elements.append(Paragraph(c, cons_style))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph('De aceptar la presente propuesta, sírvase reenviar el documento debidamente firmado y sellado por el representante autorizado.', cons_style))
    elements.append(Spacer(1, 16))
    # Firmas
    firmas_data = [
        [Paragraph('Nombre y Apellidos: ________________________________', info_style), Paragraph('Firma y Sello: ________________________________', info_style)],
        [Paragraph('Cargo: ________________________________', info_style), ''],
    ]
    firmas_table = Table(firmas_data, colWidths=[270, 230])
    firmas_table.setStyle(TableStyle([
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(KeepTogether([firmas_table]))

    # --- 8. Construir el PDF ---
    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    # Nombre del archivo
    if cotizacion.cotizacion:
        nombre_archivo = cotizacion.cotizacion.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
        filename = f"cotizacion_{nombre_archivo}.pdf"
    else:
        filename = f"cotizacion_{cotizacion.pk}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
@admin_required
def generate_qr_view(request):
    """Vista para generar códigos QR de cualquier URL o texto"""
    if request.method == 'POST':
        url_or_text = request.POST.get('url_or_text', '').strip()
        qr_size = int(request.POST.get('qr_size', 150))
        export_format = request.POST.get('export_format', 'PNG')
        
        print(f"DEBUG: URL/Text: {url_or_text}")
        print(f"DEBUG: QR Size: {qr_size}")
        print(f"DEBUG: Export Format: {export_format}")
        
        if url_or_text:
            try:
                # Generar el QR
                qr_img = generate_qr_code(url_or_text, qr_size, export_format)
                print(f"DEBUG: QR generado exitosamente")
            except Exception as e:
                print(f"ERROR generando QR: {e}")
                messages.error(request, f"Error generando el código QR: {e}")
                return render(request, 'core/generate_qr.html')
            
            try:
                # Exportar como imagen
                buffer = io.BytesIO()
                qr_img.save(buffer, format=export_format)
                buffer.seek(0)
                
                # Determinar el tipo MIME
                content_type = 'image/png' if export_format == 'PNG' else 'image/jpeg'
                file_extension = 'png' if export_format == 'PNG' else 'jpg'
                
                response = HttpResponse(buffer.getvalue(), content_type=content_type)
                response['Content-Disposition'] = f'attachment; filename="codigo_qr.{file_extension}"'
                return response
            except Exception as e:
                print(f"ERROR guardando imagen: {e}")
                messages.error(request, f"Error guardando la imagen: {e}")
                return render(request, 'core/generate_qr.html')
    
    return render(request, 'core/generate_qr.html')


# ========================================================
# VISTAS DEL SISTEMA DE CALENDARIO Y RECORDATORIOS
# ========================================================

@login_required
@admin_required
def calendario_view(request):
    """Vista principal del calendario"""
    print("=== VISTA CALENDARIO EJECUTÁNDOSE ===")
    from datetime import datetime, date
    import calendar
    
    # Obtener mes y año de los parámetros o usar actual
    mes = int(request.GET.get('mes', datetime.now().month))
    año = int(request.GET.get('año', datetime.now().year))
    tipo_filtro = request.GET.get('tipo', '')
    
    print(f"CALENDARIO - Mes: {mes}, Año: {año}, Tipo filtro: {tipo_filtro}")
    
    # Verificar todos los eventos en la base de datos
    todos_eventos = Evento.objects.all()
    print(f"TODOS LOS EVENTOS EN BD: {todos_eventos.count()}")
    for evento in todos_eventos:
        print(f"  - {evento.titulo} | Fecha: {evento.fecha_inicio} | Activo: {evento.activo} | Creado por: {evento.creado_por}")
    
    # Crear formulario de filtro
    filtro_form = FiltroEventoForm(initial={'mes': mes, 'año': año, 'tipo': tipo_filtro})
    
    # Obtener eventos del mes
    eventos = Evento.objects.filter(
        fecha_inicio__year=año,
        fecha_inicio__month=mes,
        activo=True
    ).order_by('fecha_inicio')
    
    print(f"EVENTOS ENCONTRADOS: {eventos.count()}")
    for evento in eventos:
        print(f"  - {evento.titulo} ({evento.fecha_inicio}) - Activo: {evento.activo}")
    
    # Aplicar filtro por tipo si se especifica
    if tipo_filtro:
        eventos = eventos.filter(tipo=tipo_filtro)
        print(f"EVENTOS DESPUÉS DEL FILTRO: {eventos.count()}")
    
    # Crear calendario
    cal = calendar.monthcalendar(año, mes)
    nombre_mes = calendar.month_name[mes]
    
    # Organizar eventos por día
    eventos_por_dia = {}
    for evento in eventos:
        dia = evento.fecha_inicio.day
        if dia not in eventos_por_dia:
            eventos_por_dia[dia] = []
        eventos_por_dia[dia].append(evento)
    
    print(f"EVENTOS POR DÍA: {eventos_por_dia}")
    
    context = {
        'calendario': cal,
        'nombre_mes': nombre_mes,
        'año': año,
        'mes': mes,
        'eventos_por_dia': eventos_por_dia,
        'filtro_form': filtro_form,
        'tipos_evento': Evento.TIPO_CHOICES,
    }
    
    return render(request, 'core/calendario.html', context)


@login_required
@admin_required
def evento_create_view(request):
    print(f"MÉTODO: {request.method}")
    if request.method == 'POST':
        print('LLEGA AL POST')
        print(f"POST DATA: {request.POST}")
        print(f"FILES: {request.FILES}")
        form = EventoForm(request.POST)
        print(f"FORMULARIO CREADO: {form}")
        print(f"FORMULARIO VÁLIDO: {form.is_valid()}")
        if form.is_valid():
            print('FORMULARIO VÁLIDO')
            print(f"DATOS LIMPIOS: {form.cleaned_data}")
            evento = form.save(commit=False)
            evento.creado_por = request.user
            evento.save()
            print(f"EVENTO GUARDADO: {evento.pk}")
            messages.success(request, f'Evento "{evento.titulo}" creado exitosamente.')
            return redirect('calendario')
        else:
            print('FORMULARIO INVÁLIDO')
            print(f"ERRORES: {form.errors}")
            print(f"ERRORES NO FIELD: {form.non_field_errors()}")
    else:
        print('MÉTODO GET')
        form = EventoForm()
    
    context = {
        'form': form, 
        'titulo': 'Nuevo Evento', 
        'accion': 'Guardar'
    }
    print(f"RENDERIZANDO CON CONTEXT: {context}")
    return render(request, 'core/evento_form.html', context)


@login_required
@admin_required
def evento_update_view(request, pk):
    """Editar evento existente"""
    evento = get_object_or_404(Evento, pk=pk)
    
    if request.method == 'POST':
        form = EventoForm(request.POST, instance=evento)
        if form.is_valid():
            form.save()
            messages.success(request, f'Evento "{evento.titulo}" actualizado exitosamente.')
            return redirect('calendario')
    else:
        form = EventoForm(instance=evento)
    
    context = {
        'form': form,
        'evento': evento,
        'titulo': 'Editar Evento',
        'accion': 'Actualizar'
    }
    return render(request, 'core/evento_form.html', context)


@login_required
@admin_required
def evento_delete_view(request, pk):
    """Eliminar evento"""
    evento = get_object_or_404(Evento, pk=pk)
    
    if request.method == 'POST':
        titulo_evento = evento.titulo
        evento.delete()
        messages.success(request, f'Evento "{titulo_evento}" eliminado exitosamente.')
        return redirect('calendario')
    
    context = {
        'evento': evento,
        'titulo': 'Eliminar Evento'
    }
    return render(request, 'core/evento_confirm_delete.html', context)


@login_required
@admin_required
def evento_detail_view(request, pk):
    """Ver detalles del evento"""
    evento = get_object_or_404(Evento, pk=pk)
    
    context = {
        'evento': evento,
        'titulo': 'Detalles del Evento'
    }
    return render(request, 'core/evento_detail.html', context)


@login_required
@admin_required
def logs_recordatorios_view(request):
    """Ver logs de recordatorios enviados"""
    logs = LogRecordatorio.objects.all().order_by('-fecha_envio')
    
    # Paginación
    paginator = Paginator(logs, 20)
    page = request.GET.get('page')
    try:
        logs_paginados = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        logs_paginados = paginator.page(1)
    
    context = {
        'logs': logs_paginados,
        'titulo': 'Logs de Recordatorios'
    }
    return render(request, 'core/logs_recordatorios.html', context)


@login_required
@admin_required
def enviar_recordatorios_manual_view(request):
    """Vista para enviar recordatorios manualmente (para pruebas)"""
    from django.utils import timezone
    
    # Obtener eventos que necesitan recordatorio
    eventos_pendientes = Evento.objects.filter(
        activo=True,
        recordatorio_enviado=False
    )
    
    recordatorios_enviados = 0
    
    for evento in eventos_pendientes:
        if evento.debe_enviar_recordatorio:
            # Aquí iría la lógica de envío
            # Por ahora solo marcamos como enviado
            evento.marcar_recordatorio_enviado()
            recordatorios_enviados += 1
    
    messages.success(request, f'Se enviaron {recordatorios_enviados} recordatorios.')
    return redirect('calendario')
