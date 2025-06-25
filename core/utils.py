import random
import string
from django.utils.text import slugify
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import qrcode
import io
from reportlab.lib.utils import ImageReader


def send_email(user, subject, msg):
    send_mail(
        subject,
        msg,
        settings.EMAIL_FROM_ADDRESS,
        [user.email],
        fail_silently=False,
    )


def send_html_email(subject, recipient_list, template, context):
    """A function responsible for sending HTML email"""
    # Render the HTML template
    html_message = render_to_string(template, context)

    # Generate plain text version of the email (optional)
    plain_message = strip_tags(html_message)

    # Send the email
    send_mail(
        subject,
        plain_message,
        settings.EMAIL_FROM_ADDRESS,
        recipient_list,
        html_message=html_message,
    )


def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))


def unique_slug_generator(instance, new_slug=None):
    """
    Assumes the instance has a model with a slug field and a title
    character (char) field.
    """
    if new_slug is not None:
        slug = new_slug
    else:
        slug = slugify(instance.title)

    klass = instance.__class__
    qs_exists = klass.objects.filter(slug=slug).exists()
    if qs_exists:
        new_slug = f"{slug}-{random_string_generator(size=4)}"
        return unique_slug_generator(instance, new_slug=new_slug)
    return slug


def generate_qr_code(data, size=65, format='PNG'):
    """
    Genera un código QR para cualquier dato (URL, texto, etc.)
    
    Args:
        data (str): El contenido para el código QR (URL, texto, etc.)
        size (int): Tamaño del QR en píxeles (por defecto 65)
        format (str): Formato de imagen ('PNG', 'JPEG', 'PDF')
    
    Returns:
        ImageReader: Objeto ImageReader listo para usar en ReportLab (para PDF)
        PIL.Image: Imagen PIL para exportar como PNG/JPEG
    """
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
    if size != 65:
        qr_image = qr_image.resize((size, size))
    
    if format in ['PNG', 'JPEG']:
        # Para PNG y JPEG, devolver la imagen PIL directamente
        return qr_image
    else:
        # Para PDF, convertir a ImageReader
        qr_buffer = io.BytesIO()
        qr_image.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        return ImageReader(qr_buffer)


def generate_qr_for_drive(drive_url, size=65):
    """
    Genera QR específicamente para enlaces de Google Drive
    """
    return generate_qr_code(drive_url, size)


def generate_qr_for_dropbox(dropbox_url, size=65):
    """
    Genera QR específicamente para enlaces de Dropbox
    """
    return generate_qr_code(dropbox_url, size)


def generate_qr_for_social_media(profile_url, size=65):
    """
    Genera QR para perfiles de redes sociales
    """
    return generate_qr_code(profile_url, size)
