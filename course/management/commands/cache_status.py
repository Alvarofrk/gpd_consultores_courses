"""
Comando para verificar el estado del caché
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings


class Command(BaseCommand):
    help = 'Verifica el estado del caché del sistema'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Verificando estado del caché...")
        
        # Verificar configuración de caché
        cache_config = getattr(settings, 'CACHES', {})
        if cache_config:
            self.stdout.write(f"✅ Configuración de caché encontrada:")
            for cache_name, config in cache_config.items():
                self.stdout.write(f"   - {cache_name}: {config['BACKEND']}")
        else:
            self.stdout.write("❌ No hay configuración de caché")
        
        # Probar caché
        try:
            # Test básico
            cache.set('test_key', 'test_value', 30)
            test_value = cache.get('test_key')
            
            if test_value == 'test_value':
                self.stdout.write("✅ Caché funcionando correctamente")
            else:
                self.stdout.write("❌ Caché no está funcionando correctamente")
            
            # Limpiar test
            cache.delete('test_key')
            
        except Exception as e:
            self.stdout.write(f"❌ Error al probar caché: {e}")
        
        # Verificar caché de cursos
        try:
            from course.optimizations import CourseCache
            
            # Probar métodos de caché
            test_user_id = 1
            cache_key = CourseCache.get_bulk_progress_cache_key(test_user_id)
            self.stdout.write(f"✅ Clave de caché generada: {cache_key}")
            
        except Exception as e:
            self.stdout.write(f"❌ Error al verificar CourseCache: {e}")
        
        self.stdout.write("🏁 Verificación completada")
