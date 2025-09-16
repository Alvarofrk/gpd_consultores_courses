#!/usr/bin/env python
"""
Comando de gestión para sincronizar el progreso de videos y documentos
Marca automáticamente como completados los documentos relacionados a videos ya completados
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from course.models import Course, UploadVideo, Upload, VideoCompletion, DocumentCompletion
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Sincroniza el progreso de videos y documentos para usuarios existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se haría sin hacer cambios reales',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Sincronizar solo para un usuario específico',
        )
        parser.add_argument(
            '--course-id',
            type=int,
            help='Sincronizar solo para un curso específico',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        user_id = options.get('user_id')
        course_id = options.get('course_id')

        self.stdout.write(
            self.style.SUCCESS('🔄 Iniciando sincronización de progreso de videos y documentos...')
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('⚠️  MODO DRY-RUN: No se realizarán cambios reales')
            )

        # Obtener usuarios a procesar
        if user_id:
            users = User.objects.filter(id=user_id, is_student=True)
            if not users.exists():
                raise CommandError(f'No se encontró usuario con ID {user_id}')
        else:
            users = User.objects.filter(is_student=True)

        # Obtener cursos a procesar
        if course_id:
            courses = Course.objects.filter(id=course_id)
            if not courses.exists():
                raise CommandError(f'No se encontró curso con ID {course_id}')
        else:
            courses = Course.objects.all()

        total_synced = 0
        total_users = users.count()
        total_courses = courses.count()

        self.stdout.write(f'📊 Procesando {total_users} usuarios en {total_courses} cursos...')

        for user in users:
            user_synced = 0
            self.stdout.write(f'\n👤 Procesando usuario: {user.username}')

            for course in courses:
                course_synced = self.sync_user_course_progress(user, course, dry_run)
                user_synced += course_synced

            if user_synced > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Usuario {user.username}: {user_synced} documentos sincronizados')
                )
            else:
                self.stdout.write(f'ℹ️  Usuario {user.username}: Sin cambios necesarios')

            total_synced += user_synced

        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Sincronización completada: {total_synced} documentos sincronizados')
        )

    def sync_user_course_progress(self, user, course, dry_run=False):
        """
        Sincroniza el progreso de un usuario en un curso específico
        """
        # Obtener videos completados por el usuario en este curso
        completed_videos = VideoCompletion.objects.filter(
            user=user,
            video__course=course
        ).select_related('video')

        if not completed_videos.exists():
            return 0

        # Obtener todos los documentos del curso
        course_documents = Upload.objects.filter(course=course).order_by('upload_time')
        documents_list = list(course_documents)

        # Obtener documentos ya completados por el usuario
        completed_document_ids = set(
            DocumentCompletion.objects.filter(
                user=user,
                document__course=course
            ).values_list('document_id', flat=True)
        )

        synced_count = 0

        # Para cada video completado, marcar su documento relacionado como completado
        for video_completion in completed_videos:
            video = video_completion.video
            
            # Encontrar el índice del video en la lista de videos del curso
            course_videos = UploadVideo.objects.filter(course=course).order_by('order', 'timestamp')
            videos_list = list(course_videos)
            
            try:
                video_index = videos_list.index(video)
            except ValueError:
                # Video no encontrado en la lista actual
                continue

            # Verificar si hay un documento en el mismo índice
            if video_index < len(documents_list):
                related_document = documents_list[video_index]
                
                # Si el documento no está completado, marcarlo como completado
                if related_document.id not in completed_document_ids:
                    if not dry_run:
                        with transaction.atomic():
                            DocumentCompletion.objects.get_or_create(
                                user=user,
                                document=related_document
                            )
                    
                    synced_count += 1
                    self.stdout.write(
                        f'  📄 Marcando documento "{related_document.title}" como completado '
                        f'(relacionado con video "{video.title}")'
                    )

        return synced_count

    def get_course_video_document_mapping(self, course):
        """
        Obtiene el mapeo de videos a documentos en un curso
        """
        videos = UploadVideo.objects.filter(course=course).order_by('order', 'timestamp')
        documents = Upload.objects.filter(course=course).order_by('upload_time')
        
        return list(videos), list(documents)
