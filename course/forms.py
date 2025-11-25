from django import forms
from django.core.exceptions import ValidationError
from accounts.models import User
from .models import Program, Course, CourseAllocation, Upload, UploadVideo
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update({"class": "form-control"})
        self.fields["summary"].widget.attrs.update({"class": "form-control"})


class CourseAddForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = "__all__"
        exclude = ['slug', 'last_cert_code']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update({"class": "form-control"})
        self.fields["code"].widget.attrs.update({"class": "form-control"})
        self.fields["credit"].widget.attrs.update({"class": "form-control"})
        self.fields["summary"].widget.attrs.update({"class": "form-control"})
        self.fields["program"].widget.attrs.update({"class": "form-control"})
        self.fields["level"].widget.attrs.update({"class": "form-control"})
        self.fields["year"].widget.attrs.update({"class": "form-control"})
        self.fields["semester"].widget.attrs.update({"class": "form-control"})
        self.fields["is_elective"].widget.attrs.update({"class": "form-check-input"})
        self.fields["is_active"].widget.attrs.update({"class": "form-check-input"})
        self.fields["is_external"].widget.attrs.update({"class": "form-check-input"})

        # Configurar las opciones para los campos de selección
        self.fields["level"].choices = settings.LEVEL_CHOICES
        self.fields["year"].choices = settings.YEARS
        self.fields["semester"].choices = settings.SEMESTER_CHOICES

        # Hacer que los campos requeridos sean obligatorios
        self.fields["title"].required = True
        self.fields["code"].required = True
        self.fields["credit"].required = True
        self.fields["program"].required = True
        self.fields["level"].required = True
        self.fields["year"].required = True
        self.fields["semester"].required = True

        # Agregar mensajes de ayuda
        self.fields["summary"].help_text = _("Máximo 200 caracteres")
        self.fields["code"].help_text = _("Código único del curso")
        self.fields["is_external"].help_text = _("Activa esta opción si el certificado se gestionará externamente (Google Drive).")

    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data.get('code')
        title = cleaned_data.get('title')
        
        # Verificar si el código ya existe
        if code:
            if Course.objects.filter(code=code).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise ValidationError({
                    'code': _('Este código de curso ya existe.')
                })
        
        # Verificar si el título ya existe
        if title:
            if Course.objects.filter(title=title).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise ValidationError({
                    'title': _('Este título de curso ya existe.')
                })
        
        return cleaned_data

    def clean_credit(self):
        credit = self.cleaned_data.get('credit')
        if credit is not None and credit < 0:
            raise ValidationError(_('Los créditos no pueden ser negativos.'))
        return credit

    def clean_summary(self):
        summary = self.cleaned_data.get('summary')
        if summary and len(summary) > 200:
            raise ValidationError(_('El resumen no puede tener más de 200 caracteres.'))
        return summary


class CourseAllocationForm(forms.ModelForm):
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all().order_by("level"),
        widget=forms.CheckboxSelectMultiple(
            attrs={"class": "browser-default checkbox"}
        ),
        required=True,
    )
    lecturer = forms.ModelChoiceField(
        queryset=User.objects.filter(is_lecturer=True),
        widget=forms.Select(attrs={"class": "browser-default custom-select"}),
        label="lecturer",
    )

    class Meta:
        model = CourseAllocation
        fields = ["lecturer", "courses"]

    def __init__(self, *args, **kwargs):
        super(CourseAllocationForm, self).__init__(*args, **kwargs)
        self.fields["lecturer"].queryset = User.objects.filter(is_lecturer=True)


class EditCourseAllocationForm(forms.ModelForm):
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all().order_by("level"),
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )
    lecturer = forms.ModelChoiceField(
        queryset=User.objects.filter(is_lecturer=True),
        widget=forms.Select(attrs={"class": "browser-default custom-select"}),
        label="lecturer",
    )

    class Meta:
        model = CourseAllocation
        fields = ["lecturer", "courses"]

    def __init__(self, *args, **kwargs):
        super(EditCourseAllocationForm, self).__init__(*args, **kwargs)
        self.fields["lecturer"].queryset = User.objects.filter(is_lecturer=True)


# Formulario para subir archivos a un curso específico
class UploadFormFile(forms.ModelForm):
    upload_type = forms.ChoiceField(
        choices=[
            ('url', 'Usar enlace externo (Google Drive, Dropbox, etc.)')
        ],
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        initial='url',
        label="Tipo de subida"
    )
    
    class Meta:
        model = Upload
        fields = (
            "title",
            "file",
            "external_url",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update({"class": "form-control"})
        self.fields["file"].widget.attrs.update({"class": "form-control"})
        self.fields["external_url"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "https://drive.google.com/file/d/.../view?usp=sharing"
        })
        self.fields["external_url"].required = False
        
        # Agregar JavaScript para mostrar/ocultar campos según el tipo
        self.fields["upload_type"].widget.attrs.update({
            "onchange": "toggleUploadFields()"
        })

    def clean(self):
        cleaned_data = super().clean()
        upload_type = cleaned_data.get('upload_type')
        external_url = cleaned_data.get('external_url')
        
        # Solo validar URL ya que no hay opción de archivo
        if upload_type == 'url' and not external_url:
            raise ValidationError('Debes proporcionar una URL externa.')
        
        return cleaned_data

    def clean_external_url(self):
        url = self.cleaned_data.get('external_url')
        if url:
            # Validar que sea una URL válida
            if not url.startswith(('http://', 'https://')):
                raise ValidationError('La URL debe comenzar con http:// o https://')
            
            # Validar URLs de Google Drive
            if 'drive.google.com' in url:
                if '/view?' in url:
                    # Convertir URL de visualización a URL de preview
                    url = url.replace('/view?', '/preview?')
                elif '/preview?' not in url:
                    raise ValidationError('Para Google Drive, usa el enlace de "Vista previa" o "Compartir"')
        
        return url



# Formulario para agregar videos usando URLs de Vimeo
class UploadFormVideo(forms.ModelForm):
    class Meta:
        model = UploadVideo
        fields = (
            "title",
            "vimeo_url",
            "youtube_url",
            "order",
            "summary",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update({"class": "form-control"})
        self.fields["vimeo_url"].widget.attrs.update({"class": "form-control"})
        self.fields["youtube_url"].widget.attrs.update({"class": "form-control"})
        self.fields["order"].widget.attrs.update({"class": "form-control"})
        self.fields["summary"].widget.attrs.update({"class": "form-control"})

    def clean(self):
        cleaned_data = super().clean()
        vimeo_url = cleaned_data.get('vimeo_url')
        youtube_url = cleaned_data.get('youtube_url')

        if not vimeo_url and not youtube_url:
            raise ValidationError('Debes proporcionar al menos una URL de video (Vimeo o YouTube).')

        if vimeo_url and youtube_url:
            raise ValidationError('Solo puedes proporcionar una URL de video (Vimeo o YouTube), no ambas.')

        return cleaned_data

    def clean_vimeo_url(self):
        url = self.cleaned_data.get('vimeo_url')
        if url and 'vimeo.com' not in url:
            raise ValidationError('Por favor, ingresa una URL válida de Vimeo.')
        return url

    def clean_youtube_url(self):
        url = self.cleaned_data.get('youtube_url')
        if url and not any(domain in url for domain in ['youtube.com', 'youtu.be']):
            raise ValidationError('Por favor, ingresa una URL válida de YouTube.')
        return url