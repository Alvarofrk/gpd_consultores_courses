from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django import forms
from django.db import transaction
from django.http import HttpResponse, HttpResponseNotAllowed
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from io import BytesIO
from datetime import datetime
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from accounts.decorators import admin_required, lecturer_required
from accounts.models import User, Student
from .forms import SessionForm, SemesterForm, NewsAndEventsForm, CotizacionForm, ItemCotizacionFormSet
from .models import NewsAndEvents, ActivityLog, Session, Semester, Cotizacion, ItemCotizacion, HistorialEstado


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
    cotizaciones = Cotizacion.objects.all().order_by('-fecha_cotizacion')
    
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
                        for instance in instances:
                            # Guardar solo si hay algún campo relevante lleno
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
                        for error in formset.errors:
                            if error:
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
                        # Guardar solo los ítems con datos relevantes
                        for instance in instances:
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
                for error in formset.errors:
                    if error:
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
    """Generar y descargar PDF de la cotización con estilo corporativo"""
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # LOGOS ARRIBA (doble de tamaño, ajuste fino)
    try:
        p.drawImage('static/img/logo1.jpg', 30, height-100, width=240, height=100, preserveAspectRatio=True, mask='auto')
    except:
        pass
    try:
        p.drawImage('static/img/iso.PNG', width-240, height-90, width=160, height=80, preserveAspectRatio=True, mask='auto')
    except:
        pass

    # TÍTULO Y SUBTÍTULO DEBAJO DE LOS LOGOS
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(width/2, height-105, '“AÑO DE LA RECUPERACIÓN Y CONSOLIDACIÓN DE LA ECONOMÍA PERUANA”')
    p.setFont("Helvetica", 8)
    p.drawString(30, height-120, "Residencial los Álamos Mz. A5 piso Nº 3 – Cerro Colorado")
    p.drawString(30, height-130, "RUC: 20604885141")
    p.drawString(30, height-140, "944 065 297 – 991 087 490")
    p.drawString(30, height-150, "ventas@gpdconsultoressac.com")
    p.setFont("Helvetica-Oblique", 8)
    p.drawString(width-220, height-120, "Elaborado por: Área Comercial")
    p.drawString(width-220, height-130, "Aprobado por: Gerente General")

    # LÍNEA AZUL
    p.setStrokeColorRGB(0.1, 0.3, 0.6)
    p.setLineWidth(2)
    p.line(30, height-160, width-30, height-160)

    # DATOS DE COTIZACIÓN Y CLIENTE (alineados en filas)
    p.setFont("Helvetica-Bold", 9)
    y_datos = height-175
    p.drawString(35, y_datos, "Dirigido a:")
    p.drawString(35, y_datos-15, "Empresa:")
    p.drawString(35, y_datos-30, "RUC:")
    p.setFont("Helvetica", 9)
    p.drawString(100, y_datos, cotizacion.dirigido_a or "-")
    p.drawString(100, y_datos-15, cotizacion.empresa or "-")
    p.drawString(100, y_datos-30, cotizacion.ruc or "-")

    # DATOS DE COTIZACIÓN (alineados en filas, no encimados)
    p.setFont("Helvetica-Bold", 9)
    x2 = width/2+10
    y_cot = y_datos
    p.drawString(x2, y_cot, "Cotización:")
    p.drawString(x2, y_cot-15, "Tipo de Cotización:")
    p.drawString(x2, y_cot-30, "Fecha de Cotización:")
    p.drawString(x2, y_cot-45, "Validez de la Cotización:")
    p.setFont("Helvetica", 9)
    p.drawString(x2+90, y_cot, cotizacion.cotizacion or "-")
    p.drawString(x2+90, y_cot-15, cotizacion.tipo_cotizacion or "-")
    p.drawString(x2+90, y_cot-30, cotizacion.fecha_cotizacion.strftime('%d/%m/%Y') if cotizacion.fecha_cotizacion else "-")
    p.drawString(x2+110, y_cot-45, cotizacion.validez_cotizacion.strftime('%d/%m/%Y') if cotizacion.validez_cotizacion else "-")
    
    # LÍNEA NARANJA
    p.setStrokeColorRGB(1, 0.5, 0)
    p.setLineWidth(2)
    p.line(30, y_datos-55, width-30, y_datos-55)

    # SERVICIO
    y_serv = y_datos-70
    p.setFont("Helvetica-Bold", 9)
    p.drawString(35, y_serv, "Servicio:")
    p.drawString(35, y_serv-15, "Modalidad:")
    p.drawString(35, y_serv-30, "Sede del servicio:")
    p.drawString(35, y_serv-45, "Fecha del servicio:")
    p.setFont("Helvetica", 9)
    p.drawString(100, y_serv, (cotizacion.servicio or "-")[:60])
    p.drawString(100, y_serv-15, cotizacion.get_modalidad_display() or "-")
    p.drawString(120, y_serv-30, cotizacion.sede_servicio or "-")
    p.drawString(120, y_serv-45, cotizacion.fecha_servicio.strftime('%d/%m/%Y') if cotizacion.fecha_servicio else "-")

    # TABLA DE ÍTEMS (posición fija para 7 ítems)
    styles = getSampleStyleSheet()
    styleN = styles["Normal"]
    styleN.fontName = 'Helvetica'
    styleN.fontSize = 8
    styleN.leading = 10
    items_data = [[
        "Descripción", "Curso", "Duración", "Precio Unit.", "Cantidad", "Inversión S/."
    ]]
    for item in cotizacion.items.all():
        desc = Paragraph(item.descripcion or "-", styleN)
        curso = Paragraph(item.curso or "-", styleN)
        items_data.append([
            desc,
            curso,
            item.duracion or "-",
            f"S/ {item.precio_unitario:.2f}",
            str(item.cantidad),
            f"S/ {item.subtotal:.2f}"
        ])
    table = Table(items_data, colWidths=[150, 100, 60, 70, 60, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a3764')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
    ]))
    # Calcular la altura de la tabla con 7 ítems
    dummy_data = [["-", "-", "-", "-", "-", "-"] for _ in range(7)]
    dummy_table = Table([items_data[0]] + dummy_data, colWidths=[150, 100, 60, 70, 60, 80])
    dummy_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a3764')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
    ]))
    # Calcular la altura de la tabla con 7 ítems
    dummy_data = [["-", "-", "-", "-", "-", "-"] for _ in range(7)]
    dummy_table = Table([items_data[0]] + dummy_data, colWidths=[150, 100, 60, 70, 60, 80])
    dummy_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a3764')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
    ]))
    _, table_height_max = dummy_table.wrap(width-60, height)
    table_width, table_height = table.wrap(width-60, height)
    # Alinear la tabla real pegada arriba del espacio reservado para 7 ítems
    y_tabla_max = y_serv - 200
    y_tabla = y_tabla_max
    table.drawOn(p, 30, y_tabla)

    # TOTALES (siempre debajo del espacio reservado para 7 ítems)
    y_tot = y_tabla_max - table_height_max + 120
    p.setFont("Helvetica-Bold", 9)
    p.drawString(width-300, y_tot, "TOTAL, S/:")
    p.setFont("Helvetica", 9)
    p.drawString(width-180, y_tot, f"S/ {cotizacion.monto_total:.2f}")
    p.setFont("Helvetica-Bold", 8)
    p.drawString(width-300, y_tot-15, "SUBTOTAL")
    p.drawString(width-300, y_tot-30, "SUBTOTAL + IGV")
    p.drawString(width-300, y_tot-45, "12% DE DETRACCIÓN - Banco de la Nación*")
    p.drawString(width-300, y_tot-60, "INVERSIÓN TOTAL A DEPOSITAR")

    # MEDIOS DE PAGO (justo debajo de totales)
    y_pago = y_tot-90
    p.setFillColor(colors.HexColor('#1a3764'))
    p.setStrokeColor(colors.HexColor('#1a3764'))
    p.setLineWidth(1.2)
    p.rect(30, y_pago, width-60, 18, fill=1, stroke=0)  # Barra azul
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 9)
    p.drawString(35, y_pago+3, "MEDIOS DE PAGO")
    p.setFillColor(colors.black)
    p.setFont("Helvetica", 8)
    y_pago_txt = y_pago-10
    p.drawString(35, y_pago_txt, "Tiempo de entrega:")
    p.drawString(130, y_pago_txt, cotizacion.tiempo_entrega or "-")
    p.drawString(35, y_pago_txt-10, "Modalidad de pago:")
    p.drawString(130, y_pago_txt-10, cotizacion.get_modalidad_pago_display() or "-")
    p.drawString(35, y_pago_txt-20, "Cuenta de ahorros BCP:")
    p.drawString(180, y_pago_txt-20, "215-95088021-001")
    p.drawString(35, y_pago_txt-30, "Cuenta CCI:")
    p.drawString(180, y_pago_txt-30, "00221519508802100123")
    p.drawString(35, y_pago_txt-40, "CUENTA de detracciones Banco de la Nación-SOLES:")
    p.drawString(280, y_pago_txt-40, "00-113-039019")

    # CONSIDERACIONES GENERALES (justo debajo de medios de pago)
    y_cons = y_pago_txt-60
    p.setFont("Helvetica-BoldOblique", 8)
    p.drawString(35, y_cons, u"Consideraciones generales del servicio")
    p.setFont("Helvetica", 7)
    consideraciones = [
        "1. Se tomará en cuenta la asistencia y la nota mínima de aprobación que es 14 (70%)",
        "2. G.P.D Consultores brinda: Certificado de cada curso para los participantes, material didáctico, acceso a nuestra página web.",
        "3. El servicio se brindará con un aviso mínimo de 48 horas de anticipación y previa confirmación del pago, ya sea parcial o total.",
        "4. Cambios de fecha y cancelaciones: Cualquier cambio debe notificarse 48 horas antes del curso, aplicando una penalización del 30% sobre el monto acordado.",
        "5. Confirmación de acuerdos: Todos los compromisos serán válidos únicamente si son confirmados por correo electrónico por un representante autorizado de GPD CONSULTORES."
    ]
    y = y_cons-15
    for c in consideraciones:
        p.drawString(40, y, c)
        y -= 12
    p.setFont("Helvetica-Bold", 8)
    p.drawString(35, y-10, u"De aceptar la presente propuesta, sírvase reenviar el documento debidamente firmado y sellado por el representante autorizado.")

    # LÍNEAS DE FIRMA (justo debajo de consideraciones)
    from reportlab.lib.colors import black
    p.setStrokeColor(black)
    p.setLineWidth(1)
    p.setFont("Helvetica", 8)
    p.drawString(35, y-40, "Nombre y Apellidos:")
    p.line(120, y-42, 270, y-42)
    p.drawString(35, y-55, "Cargo:")
    p.line(120, y-57, 270, y-57)
    p.drawString(width-200, y-40, "Firma y Sello")
    p.line(width-140, y-42, width-40, y-42)

    p.showPage()
    p.save()
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="cotizacion_{cotizacion.pk}.pdf"'
    return response
