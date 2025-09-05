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
            
            if total_content == 0:
                progress = 0
            else:
                completed_content = course_data['completed_videos'] + course_data['completed_documents']
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
        Invalida caché de progreso del usuario
        Si course_id es None, invalida todos los cursos del usuario
        """
        if course_id:
            cache.delete(CourseCache.get_user_progress_cache_key(user_id, course_id))
        else:
            # Invalidar caché bulk de progreso
            cache.delete(CourseCache.get_bulk_progress_cache_key(user_id))
    
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
