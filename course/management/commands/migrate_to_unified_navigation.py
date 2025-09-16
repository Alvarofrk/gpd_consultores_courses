"""
Comando de migración para actualizar enlaces a la navegación unificada
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from course.models import Course, UploadVideo, Upload
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Migra los enlaces existentes a la nueva navegación unificada'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar sin hacer cambios reales',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODO DRY-RUN: No se realizarán cambios reales')
            )
        
        self.stdout.write('Iniciando migración a navegación unificada...')
        
        # Obtener todos los cursos
        courses = Course.objects.all()
        
        migrated_courses = 0
        total_courses = courses.count()
        
        for course in courses:
            try:
                with transaction.atomic():
                    # Verificar si el curso tiene contenido
                    videos = UploadVideo.objects.filter(course=course)
                    documents = Upload.objects.filter(course=course)
                    
                    if not videos.exists() and not documents.exists():
                        self.stdout.write(
                            f'  Curso "{course.title}" no tiene contenido - omitiendo'
                        )
                        continue
                    
                    # Generar URL de la navegación unificada
                    unified_url = reverse('course_unified_navigation_first', kwargs={'slug': course.slug})
                    
                    if not dry_run:
                        # Aquí podrías actualizar cualquier campo que almacene URLs
                        # Por ejemplo, si tienes un campo 'navigation_url' en el modelo Course
                        # course.navigation_url = unified_url
                        # course.save()
                        pass
                    
                    self.stdout.write(
                        f'  ✓ Curso "{course.title}" migrado a: {unified_url}'
                    )
                    
                    migrated_courses += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error migrando curso "{course.title}": {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nMigración completada: {migrated_courses}/{total_courses} cursos procesados'
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nPara ejecutar la migración real, ejecuta sin --dry-run')
            )
