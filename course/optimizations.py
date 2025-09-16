"""
Optimizaciones de rendimiento para el sistema de cursos
Mantiene la funcionalidad exacta pero con consultas optimizadas
"""
from django.db.models import Count, Exists, OuterRef, Q, Prefetch
from django.core.cache import cache
from django.conf import settings
from .models import Course, UploadVideo, Upload, VideoCompletion, DocumentCompletion
from quiz.models import Quiz, Sitting


class CourseOptimizations:
    """
    Clase con métodos optimizados para operaciones de cursos
    Mantiene compatibilidad total con métodos existentes
    """
    
    @staticmethod
    def get_bulk_progress_for_courses(courses, user):
        """
        Obtiene progreso de múltiples cursos en una sola consulta
        Reemplaza múltiples llamadas a get_progress_for_user()
        """
        if not courses:
            return {}
        
        course_ids = [course.id for course in courses]
        
        # Consulta optimizada con annotate
        courses_with_progress = Course.objects.filter(
            id__in=course_ids
        ).annotate(
            total_videos=Count('uploadvideo', distinct=True),
            total_documents=Count('upload', distinct=True),
            completed_videos=Count(
                'uploadvideo__videocompletion',
                filter=Q(uploadvideo__videocompletion__user=user),
                distinct=True
            ),
            completed_documents=Count(
                'upload__documentcompletion',
                filter=Q(upload__documentcompletion__user=user),
                distinct=True
            )
        ).values(
            'id', 'total_videos', 'total_documents', 
            'completed_videos', 'completed_documents'
        )
        
        # Convertir a diccionario para acceso rápido
        progress_data = {}
        for course_data in courses_with_progress:
            course_id = course_data['id']
            total_content = course_data['total_videos'] + course_data['total_documents']
            completed_content = course_data['completed_videos'] + course_data['completed_documents']
            
            if total_content == 0:
                progress = 0
            else:
                progress = round((completed_content / total_content) * 100, 1)
            
            progress_data[course_id] = {
                'progress': progress,
                'total_videos': course_data['total_videos'],
                'total_documents': course_data['total_documents'],
                'completed_videos': course_data['completed_videos'],
                'completed_documents': course_data['completed_documents'],
                'total_content': total_content,
                'completed_content': completed_content
            }
        
        return progress_data
    
    @staticmethod
    def get_bulk_content_summary(courses):
        """
        Obtiene resumen de contenido para múltiples cursos en una sola consulta
        Reemplaza múltiples llamadas a get_content_summary()
        """
        if not courses:
            return {}
        
        course_ids = [course.id for course in courses]
        
        courses_with_content = Course.objects.filter(
            id__in=course_ids
        ).annotate(
            total_videos=Count('uploadvideo', distinct=True),
            total_documents=Count('upload', distinct=True)
        ).values(
            'id', 'total_videos', 'total_documents'
        )
        
        content_data = {}
        for course_data in courses_with_content:
            course_id = course_data['id']
            total_content = course_data['total_videos'] + course_data['total_documents']
            
            content_data[course_id] = {
                'total_videos': course_data['total_videos'],
                'total_documents': course_data['total_documents'],
                'total_content': total_content,
                'has_videos': course_data['total_videos'] > 0,
                'has_documents': course_data['total_documents'] > 0,
            }
        
        return content_data
    
    @staticmethod
    def get_bulk_course_status(courses, user):
        """
        Obtiene estado de múltiples cursos optimizado
        Reemplaza múltiples llamadas a get_course_status_for_user()
        """
        if not courses:
            return {}
        
        # Obtener progreso de todos los cursos
        progress_data = CourseOptimizations.get_bulk_progress_for_courses(courses, user)
        
        # Obtener quizzes de todos los cursos con información completa
        course_ids = [course.id for course in courses]
        quizzes = Quiz.objects.filter(
            course_id__in=course_ids,
            draft=False
        ).select_related('course').prefetch_related('question_set')
        
        quiz_data = {}
        for quiz in quizzes:
            quiz_data[quiz.course_id] = {
                'id': quiz.id,
                'pass_mark': quiz.pass_mark,
                'max_score': quiz.get_max_score
            }
        
        # Obtener sittings aprobados de todos los cursos
        approved_sittings = Sitting.objects.filter(
            user=user,
            course_id__in=course_ids,
            complete=True
        ).select_related('quiz').values(
            'course_id', 'quiz_id', 'current_score', 'quiz__pass_mark'
        )
        
        # Agrupar sittings por curso
        course_sittings = {}
        for sitting in approved_sittings:
            course_id = sitting['course_id']
            if course_id not in course_sittings:
                course_sittings[course_id] = []
            course_sittings[course_id].append(sitting)
        
        # Calcular estado para cada curso
        status_data = {}
        for course in courses:
            course_id = course.id
            progress_info = progress_data.get(course_id, {'progress': 0})
            material_progress = progress_info['progress']
            
            quiz_info = quiz_data.get(course_id)
            
            if not quiz_info:
                # Sin examen, solo material
                if material_progress == 100:
                    status = 'course_completed'
                elif material_progress > 0:
                    status = 'material_in_progress'
                else:
                    status = 'not_started'
            else:
                # Con examen - verificar estado
                if material_progress < 100:
                    status = 'material_in_progress'
                else:
                    # Material completado, verificar examen
                    course_sitting_list = course_sittings.get(course_id, [])
                    approved_sitting = None
                    attempted_sitting = False
                    
                    for sitting in course_sitting_list:
                        if sitting['quiz_id'] == quiz_info['id']:
                            attempted_sitting = True
                            # Verificar si aprobó
                            pass_mark = sitting['quiz__pass_mark']
                            max_score = quiz_info['max_score']
                            required_score = pass_mark * max_score / 100
                            
                            if sitting['current_score'] >= required_score:
                                approved_sitting = sitting
                                break
                    
                    if approved_sitting:
                        status = 'course_completed'  # Material + Examen aprobado
                    elif attempted_sitting:
                        status = 'exam_failed'  # Intentó pero no aprobó
                    else:
                        status = 'exam_available'  # Puede hacer examen
            
            status_data[course_id] = status
        
        return status_data
    
    @staticmethod
    def get_bulk_exam_info(courses, user):
        """
        Obtiene información de exámenes para múltiples cursos optimizado
        Reemplaza múltiples llamadas a get_exam_info_for_user()
        """
        if not courses:
            return {}
        
        course_ids = [course.id for course in courses]
        
        # Obtener quizzes de todos los cursos con información completa
        quizzes = Quiz.objects.filter(
            course_id__in=course_ids,
            draft=False
        ).select_related('course').prefetch_related('question_set')
        
        quiz_data = {}
        for quiz in quizzes:
            quiz_data[quiz.course_id] = {
                'id': quiz.id,
                'pass_mark': quiz.pass_mark,
                'title': quiz.title,
                'single_attempt': quiz.single_attempt,
                'max_score': quiz.get_max_score
            }
        
        # Obtener todos los sittings de los cursos
        sittings = Sitting.objects.filter(
            user=user,
            course_id__in=course_ids,
            complete=True
        ).select_related('quiz').values(
            'course_id', 'quiz_id', 'current_score', 'end', 'fecha_aprobacion',
            'quiz__pass_mark', 'quiz__title', 'quiz__single_attempt'
        ).order_by('-end')
        
        # Agrupar sittings por curso
        course_sittings = {}
        for sitting in sittings:
            course_id = sitting['course_id']
            if course_id not in course_sittings:
                course_sittings[course_id] = []
            course_sittings[course_id].append(sitting)
        
        # Calcular información de examen para cada curso
        exam_data = {}
        for course in courses:
            course_id = course.id
            quiz_info = quiz_data.get(course_id)
            
            if not quiz_info:
                exam_data[course_id] = None
                continue
            
            course_sitting_list = course_sittings.get(course_id, [])
            relevant_sittings = [s for s in course_sitting_list if s['quiz_id'] == quiz_info['id']]
            
            if not relevant_sittings:
                exam_data[course_id] = {
                    'has_exam': True,
                    'attempted': False,
                    'passed': False,
                    'best_score': 0,
                    'attempts': 0,
                    'can_retake': True,
                    'pass_mark': quiz_info['pass_mark'],
                    'quiz_title': quiz_info['title']
                }
            else:
                best_sitting = relevant_sittings[0]  # Ya ordenado por -end
                
                # Calcular si aprobó
                pass_mark = best_sitting['quiz__pass_mark']
                max_score = quiz_info['max_score']
                required_score = pass_mark * max_score / 100
                passed = best_sitting['current_score'] >= required_score
                
                # Calcular porcentaje
                if max_score > 0:
                    best_score = (best_sitting['current_score'] / max_score) * 100
                else:
                    best_score = 0
                
                exam_data[course_id] = {
                    'has_exam': True,
                    'attempted': True,
                    'passed': passed,
                    'best_score': round(best_score, 1),
                    'attempts': len(relevant_sittings),
                    'can_retake': not quiz_info['single_attempt'] and not passed,
                    'pass_mark': quiz_info['pass_mark'],
                    'quiz_title': quiz_info['title'],
                    'last_attempt': best_sitting['end'],
                    'fecha_aprobacion': best_sitting['fecha_aprobacion'] if passed else None
                }
        
        return exam_data
    
    @staticmethod
    def get_optimized_videos_with_completion(course, user):
        """
        Obtiene videos con información de completado optimizada
        Reemplaza la conversión a lista y consultas individuales
        """
        # Consulta optimizada con annotate para verificar completado
        videos = UploadVideo.objects.filter(
            course=course
        ).annotate(
            is_completed=Exists(
                VideoCompletion.objects.filter(
                    video=OuterRef('pk'),
                    user=user
                )
            )
        ).order_by("order", "timestamp")
        
        return videos
    
    @staticmethod
    def get_optimized_documents_with_completion(course, user):
        """
        Obtiene documentos con información de completado optimizada
        """
        documents = Upload.objects.filter(
            course=course
        ).annotate(
            is_completed=Exists(
                DocumentCompletion.objects.filter(
                    document=OuterRef('pk'),
                    user=user
                )
            )
        ).order_by("upload_time")
        
        return documents


class CourseUnifiedNavigation:
    """
    Clase para manejar la navegación unificada entre videos y documentos
    """
    
    @staticmethod
    def sync_document_completion_when_video_completed(user, video):
        """
        Marca automáticamente como completado el documento relacionado cuando se completa un video
        Mantiene la sincronización entre videos y documentos por índice
        """
        from .models import DocumentCompletion
        
        # Obtener todos los videos del curso ordenados
        course_videos = UploadVideo.objects.filter(course=video.course).order_by('order', 'timestamp')
        videos_list = list(course_videos)
        
        # Encontrar el índice del video completado
        try:
            video_index = videos_list.index(video)
        except ValueError:
            return False  # Video no encontrado
        
        # Obtener todos los documentos del curso ordenados
        course_documents = Upload.objects.filter(course=video.course).order_by('upload_time')
        documents_list = list(course_documents)
        
        # Verificar si hay un documento en el mismo índice
        if video_index < len(documents_list):
            related_document = documents_list[video_index]
            
            # Verificar si el documento ya está completado
            if not DocumentCompletion.objects.filter(
                user=user, 
                document=related_document
            ).exists():
                # Marcar el documento como completado
                DocumentCompletion.objects.get_or_create(
                    user=user,
                    document=related_document
                )
                return True
        
        return False
    
    @staticmethod
    def get_unified_course_content(course, user):
        """
        Obtiene todo el contenido del curso (videos + documentos) en orden unificado
        Mantiene la sincronización por índice: cada video va seguido de su documento correspondiente
        """
        videos = CourseOptimizations.get_optimized_videos_with_completion(course, user)
        documents = CourseOptimizations.get_optimized_documents_with_completion(course, user)
        
        # Convertir a listas para acceso por índice
        videos_list = list(videos)
        documents_list = list(documents)
        
        # Crear lista unificada manteniendo la sincronización por índice
        unified_content = []
        
        # Procesar videos y sus documentos correspondientes
        for video_index, video in enumerate(videos_list):
            # Agregar el video
            unified_content.append({
                'type': 'video',
                'id': video.id,
                'object': video,
                'title': video.title,
                'is_completed': getattr(video, 'is_completed', False),
                'order': video.order,
                'timestamp': video.timestamp,
                'slug': getattr(video, 'slug', None),
                'index': video_index
            })
            
            # Agregar el documento correspondiente si existe
            if video_index < len(documents_list):
                doc = documents_list[video_index]
                unified_content.append({
                    'type': 'document',
                    'id': doc.id,
                    'object': doc,
                    'title': doc.title,
                    'is_completed': getattr(doc, 'is_completed', False),
                    'order': video.order + 0.5,  # Documento va después del video
                    'timestamp': doc.upload_time,
                    'slug': None,
                    'index': video_index,
                    'related_video_id': video.id  # Referencia al video relacionado
                })
        
        # Agregar documentos que no tienen video relacionado (después de todos los videos)
        for doc_index in range(len(videos_list), len(documents_list)):
            doc = documents_list[doc_index]
            unified_content.append({
                'type': 'document',
                'id': doc.id,
                'object': doc,
                'title': doc.title,
                'is_completed': getattr(doc, 'is_completed', False),
                'order': 999 + doc_index,  # Documentos sin video van al final
                'timestamp': doc.upload_time,
                'slug': None,
                'index': doc_index,
                'related_video_id': None  # Sin video relacionado
            })
        
        # Ordenar por order y timestamp
        unified_content.sort(key=lambda x: (x['order'], x['timestamp']))
        
        return unified_content
    
    @staticmethod
    def get_current_content(unified_content, content_id, content_type):
        """
        Obtiene el contenido actual basado en ID y tipo
        """
        if content_id and content_type:
            for content in unified_content:
                if content['id'] == content_id and content['type'] == content_type:
                    return content
        
        # Si no se encuentra, devolver el primero
        return unified_content[0] if unified_content else None
    
    @staticmethod
    def get_content_index(unified_content, current_content):
        """
        Obtiene el índice del contenido actual en la lista unificada
        """
        for i, content in enumerate(unified_content):
            if (content['id'] == current_content['id'] and 
                content['type'] == current_content['type']):
                return i
        return 0
    
    @staticmethod
    def get_navigation_content(unified_content, current_content):
        """
        Obtiene el contenido anterior y siguiente
        """
        current_index = CourseUnifiedNavigation.get_content_index(unified_content, current_content)
        
        previous_content = unified_content[current_index - 1] if current_index > 0 else None
        next_content = (unified_content[current_index + 1] 
                       if current_index < len(unified_content) - 1 else None)
        
        return previous_content, next_content
    
    @staticmethod
    def validate_content_access(user, current_content, all_content):
        """
        Validación unificada que evita redirecciones cruzadas
        """
        if user.is_staff or user.is_lecturer:
            return True, None
        
        current_index = CourseUnifiedNavigation.get_content_index(all_content, current_content)
        
        # Verificar que el contenido anterior esté completado
        if current_index > 0:
            previous_content = all_content[current_index - 1]
            if not previous_content['is_completed']:
                # Retornar el contenido anterior sin completar para redirección
                return False, previous_content
        
        return True, None


class CourseCache:
    """
    Clase para manejar caché en memoria de Django
    Usa el caché local de Django (no requiere servicios externos)
    """
    
    CACHE_TIMEOUT = 300  # 5 minutos para datos dinámicos
    STATIC_CACHE_TIMEOUT = 3600  # 1 hora para datos estáticos
    
    @staticmethod
    def get_course_content_cache_key(course_id):
        return f"course_content_{course_id}"
    
    @staticmethod
    def get_user_progress_cache_key(user_id, course_id):
        return f"user_progress_{user_id}_{course_id}"
    
    @staticmethod
    def get_course_quizzes_cache_key(course_id):
        return f"course_quizzes_{course_id}"
    
    @staticmethod
    def get_bulk_progress_cache_key(user_id):
        return f"bulk_progress_{user_id}"
    
    @staticmethod
    def invalidate_user_progress_cache(user_id, course_id=None):
        """
        Invalida caché de progreso del usuario de forma selectiva
        Si course_id es None, invalida todos los cursos del usuario
        """
        if course_id:
            # Invalidar solo el curso específico (más eficiente)
            cache.delete(CourseCache.get_user_progress_cache_key(user_id, course_id))
            cache.delete(CourseCache.get_course_content_cache_key(course_id))
        else:
            # Invalidar caché bulk de progreso
            cache.delete(CourseCache.get_bulk_progress_cache_key(user_id))
    
    @staticmethod
    def invalidate_content_completion_cache(user_id, course_id, content_id, content_type):
        """
        Invalida solo el caché específico de un contenido
        Optimización máxima para actualizaciones individuales
        """
        # Invalidar caché específico del contenido
        cache_key = f"content_completion_{user_id}_{course_id}_{content_id}_{content_type}"
        cache.delete(cache_key)
        
        # Invalidar caché del curso (más selectivo que invalidar todo)
        CourseCache.invalidate_user_progress_cache(user_id, course_id)
    
    @staticmethod
    def get_cached_course_content(course_id):
        """Obtiene contenido del curso desde caché"""
        cache_key = CourseCache.get_course_content_cache_key(course_id)
        return cache.get(cache_key)
    
    @staticmethod
    def set_cached_course_content(course_id, content_data):
        """Guarda contenido del curso en caché"""
        cache_key = CourseCache.get_course_content_cache_key(course_id)
        cache.set(cache_key, content_data, CourseCache.STATIC_CACHE_TIMEOUT)
    
    @staticmethod
    def get_cached_user_progress(user_id, course_id):
        """Obtiene progreso del usuario desde caché"""
        cache_key = CourseCache.get_user_progress_cache_key(user_id, course_id)
        return cache.get(cache_key)
    
    @staticmethod
    def set_cached_user_progress(user_id, course_id, progress_data):
        """Guarda progreso del usuario en caché"""
        cache_key = CourseCache.get_user_progress_cache_key(user_id, course_id)
        cache.set(cache_key, progress_data, CourseCache.CACHE_TIMEOUT)
    
    @staticmethod
    def get_cached_bulk_progress(user_id):
        """Obtiene progreso bulk del usuario desde caché"""
        cache_key = CourseCache.get_bulk_progress_cache_key(user_id)
        return cache.get(cache_key)
    
    @staticmethod
    def set_cached_bulk_progress(user_id, progress_data):
        """Guarda progreso bulk del usuario en caché"""
        cache_key = CourseCache.get_bulk_progress_cache_key(user_id)
        cache.set(cache_key, progress_data, CourseCache.CACHE_TIMEOUT)
