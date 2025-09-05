"""
Comando para limpiar caché en producción
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Limpia todo el caché del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=int,
            help='ID del usuario específico para limpiar su caché',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Limpiar todo el caché del sistema',
        )

    def handle(self, *args, **options):
        if options['all']:
            cache.clear()
            self.stdout.write(
                self.style.SUCCESS('✅ Todo el caché ha sido limpiado')
            )
        elif options['user']:
            user_id = options['user']
            try:
                user = User.objects.get(id=user_id)
                from course.optimizations import CourseCache
                CourseCache.invalidate_user_progress_cache(user_id)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Caché del usuario {user.username} (ID: {user_id}) ha sido limpiado')
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Usuario con ID {user_id} no encontrado')
                )
        else:
            # Limpiar caché por defecto
            cache.clear()
            self.stdout.write(
                self.style.SUCCESS('✅ Caché por defecto ha sido limpiado')
            )
