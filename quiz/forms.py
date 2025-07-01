from django import forms
from django.forms.widgets import RadioSelect, Textarea
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _
from django.forms.models import inlineformset_factory
from .models import Question, Quiz, MCQuestion, Choice, ManualCertificate
import os
from django.conf import settings
from django.core.validators import ValidationError
import re


class QuestionForm(forms.Form):
    def __init__(self, question, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        choice_list = [x for x in question.get_choices_list()]
        self.fields["answers"] = forms.ChoiceField(
            choices=choice_list, widget=RadioSelect
        )


class AnexoForm(forms.Form):
    fecha_ingreso = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}), label="Fecha de Ingreso")
    ocupacion = forms.CharField(max_length=100, label="Ocupación")
    area_trabajo = forms.CharField(max_length=100, label="Área de Trabajo")
    empresa = forms.CharField(max_length=100, label="E.C.M./CONEXAS")
    distrito = forms.CharField(max_length=100, label="Distrito")
    provincia = forms.CharField(max_length=100, label="Provincia")

class EssayForm(forms.Form):
    def __init__(self, question, *args, **kwargs):
        super(EssayForm, self).__init__(*args, **kwargs)
        self.fields["answers"] = forms.CharField(
            widget=Textarea(attrs={"style": "width:100%"})
        )


class QuizAddForm(forms.ModelForm):
    class Meta:
        model = Quiz
        exclude = []
        labels = {
            'category': 'Categoría',
            'title': 'Título',
            'pass_mark': 'Nota mínima para aprobar (%)',
            'description': 'Descripción',
            'random_order': 'Orden aleatorio de preguntas',
            'answers_at_end': 'Mostrar respuestas al final',
            'exam_paper': 'Guardar resultados de cada intento',
            'single_attempt': 'Permitir solo un intento',
            'draft': 'Borrador (no visible para estudiantes)',
        }
        help_texts = {
            'category': 'Selecciona el tipo de cuestionario',
            'title': 'Introduce el título del cuestionario',
            'pass_mark': 'Porcentaje necesario para aprobar el examen',
            'description': 'Descripción detallada del cuestionario',
            'random_order': '¿Mostrar las preguntas en orden aleatorio?',
            'answers_at_end': '¿Mostrar las respuestas correctas solo al final?',
            'exam_paper': 'Si está activado, se guardarán los resultados de cada intento',
            'single_attempt': 'Si está activado, solo se permitirá un intento por usuario',
            'draft': 'Si está activado, el cuestionario no será visible para los estudiantes',
        }

    questions = forms.ModelMultipleChoiceField(
        queryset=Question.objects.all().select_subclasses(),
        required=False,
        label="Preguntas",
        widget=FilteredSelectMultiple(verbose_name="Preguntas", is_stacked=False),
    )

    def __init__(self, *args, **kwargs):
        super(QuizAddForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["questions"].initial = (
                self.instance.question_set.all().select_subclasses()
            )
        # Limitar la categoría solo a 'exam'
        self.fields['category'].choices = [
            choice for choice in self.fields['category'].choices if choice[0] == 'exam'
        ]

    def save(self, commit=True):
        quiz = super(QuizAddForm, self).save(commit=False)
        quiz.save()
        quiz.question_set.set(self.cleaned_data["questions"])
        self.save_m2m()
        return quiz


class MCQuestionForm(forms.ModelForm):
    class Meta:
        model = MCQuestion
        exclude = ()
        labels = {
            'content': 'Enunciado de la pregunta',
            'figure': 'Imagen (opcional)',
            'explanation': 'Explicación (opcional)',
            'choice_order': 'Orden de las opciones',
        }
        help_texts = {
            'content': 'Escribe el texto de la pregunta que se mostrará al usuario',
            'figure': 'Agrega una imagen si es necesario',
            'explanation': 'Explicación que se mostrará después de responder la pregunta',
            'choice_order': 'El orden en que se mostrarán las opciones de respuesta',
        }


class MCQuestionFormSet(forms.BaseInlineFormSet):
    def clean(self):
        """
        Custom validation for the formset to ensure:
        1. At least two choices are provided and not marked for deletion.
        2. At least one of the choices is marked as correct.
        """
        super().clean()

        # Collect non-deleted forms
        valid_forms = [
            form for form in self.forms if not form.cleaned_data.get("DELETE", True)
        ]

        valid_choices = [
            "choice_text" in form.cleaned_data.keys() for form in valid_forms
        ]
        if not all(valid_choices):
            raise forms.ValidationError("You must add a valid choice name.")

        # If all forms are deleted, raise a validation error
        if len(valid_forms) < 2:
            raise forms.ValidationError("You must provide at least two choices.")

        # Check if at least one of the valid forms is marked as correct
        correct_choices = [
            form.cleaned_data.get("correct", False) for form in valid_forms
        ]

        if not any(correct_choices):
            raise forms.ValidationError("One choice must be marked as correct.")

        if correct_choices.count(True) > 1:
            raise forms.ValidationError("Only one choice must be marked as correct.")


MCQuestionFormSet = inlineformset_factory(
    MCQuestion,
    Choice,
    form=MCQuestionForm,
    formset=MCQuestionFormSet,
    fields=["choice_text", "correct"],
    can_delete=True,
    extra=5,
)

class ManualCertificateForm(forms.ModelForm):
    plantilla = forms.ChoiceField(
        choices=[],
        required=True,
        help_text="Seleccione la plantilla que desea usar para el certificado"
    )
    
    class Meta:
        model = ManualCertificate
        fields = ['nombre_completo', 'dni', 'curso', 'puntaje', 'fecha_aprobacion', 'plantilla']
        widgets = {
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'dni': forms.TextInput(attrs={'class': 'form-control'}),
            'curso': forms.Select(attrs={'class': 'form-control'}),
            'puntaje': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 20}),
            'fecha_aprobacion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['plantilla'].choices = self.get_plantillas_disponibles()
    
    def get_plantillas_disponibles(self):
        plantillas = []
        pdfs_dir = os.path.join(settings.BASE_DIR, 'static', 'pdfs')
        patron = re.compile(r'^C\d+-.*\.pdf$', re.IGNORECASE)
        if os.path.exists(pdfs_dir):
            for archivo in os.listdir(pdfs_dir):
                if patron.match(archivo):
                    nombre = archivo.replace('.pdf', '')
                    plantillas.append((archivo, nombre))
        plantillas.sort(key=lambda x: x[1])
        return plantillas
    
    def clean_puntaje(self):
        puntaje = self.cleaned_data.get('puntaje')
        if puntaje < 0 or puntaje > 20:
            raise ValidationError("El puntaje debe estar entre 0 y 20")
        return puntaje
    
    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        curso = self.cleaned_data.get('curso')
        
        # Verificar si ya existe un certificado con el mismo DNI Y curso
        if ManualCertificate.objects.filter(dni=dni, curso=curso).exists():
            raise ValidationError(f"Ya existe un certificado para {dni} en el curso {curso.title}")
        
        return dni
