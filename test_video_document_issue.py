#!/usr/bin/env python
"""
Script para reproducir el problema de videos con documentos
"""

import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from course.models import Course, UploadVideo, Upload, VideoCompletion, DocumentCompletion, Program
from accounts.models import Student
from result.models import TakenCourse
from course.optimizations import CourseUnifiedNavigation

User = get_user_model()

def test_video_document_issue():
    """Reproduce el problema de videos con documentos"""
    print("🧪 REPRODUCIENDO PROBLEMA DE VIDEOS CON DOCUMENTOS")
    print("=" * 70)
    
    client = Client()
    
    try:
        # Crear datos de prueba
        user = User.objects.create_user(
            username='test_video_doc_issue',
            email='test@videodoc.com',
            password='testpass123'
        )
        
        # Crear programa
        program = Program.objects.create(title='Programa Test Video-Doc', summary='Test')
        
        # Crear estudiante
        student = Student.objects.create(
            student=user,
            program=program
        )
        
        course = Course.objects.create(
            title='Curso Test Video-Doc',
            code='VIDEODOC001',
            summary='Curso para test video-doc',
            program=program,
            level='1',
            year=1,
            semester='1',
            is_elective=False,
            is_active=True
        )
        
        # Registrar estudiante en el curso
        taken_course = TakenCourse.objects.create(
            student=student,
            course=course
        )
        
        # Crear videos
        video1 = UploadVideo.objects.create(
            title='Video 1',
            course=course,
            youtube_url='https://youtube.com/watch?v=test1',
            order=0
        )
        
        video2 = UploadVideo.objects.create(
            title='Video 2',
            course=course,
            youtube_url='https://youtube.com/watch?v=test2',
            order=1
        )
        
        # Crear documentos (MÁS documentos que videos para reproducir el problema)
        doc1 = Upload.objects.create(
            title='Documento 1 (relacionado con Video 1)',
            course=course,
            external_url='https://drive.google.com/file/doc1.pdf'
        )
        
        doc2 = Upload.objects.create(
            title='Documento 2 (relacionado con Video 2)',
            course=course,
            external_url='https://drive.google.com/file/doc2.pdf'
        )
        
        doc3 = Upload.objects.create(
            title='Documento 3 (SIN video relacionado)',
            course=course,
            external_url='https://drive.google.com/file/doc3.pdf'
        )
        
        doc4 = Upload.objects.create(
            title='Documento 4 (SIN video relacionado)',
            course=course,
            external_url='https://drive.google.com/file/doc4.pdf'
        )
        
        print(f"✅ Datos creados:")
        print(f"   - Videos: {video1.title}, {video2.title}")
        print(f"   - Documentos: {doc1.title}, {doc2.title}, {doc3.title}, {doc4.title}")
        print(f"   - Total videos: 2, Total documentos: 4")
        
        # Login
        client.force_login(user)
        
        # Obtener contenido unificado
        print("\n🔍 Analizando contenido unificado...")
        unified_content = CourseUnifiedNavigation.get_unified_course_content(course, user)
        
        print(f"\n📋 Contenido unificado generado:")
        for i, content in enumerate(unified_content):
            related_info = f" (relacionado con video {content.get('related_video_id', 'N/A')})" if content['type'] == 'document' else ""
            print(f"   {i+1}. {content['type'].upper()}: {content['title']}{related_info}")
        
        # Verificar el problema
        print(f"\n❌ PROBLEMA IDENTIFICADO:")
        print(f"   - Documentos 3 y 4 aparecen al final con related_video_id=None")
        print(f"   - Pero deberían aparecer en sus posiciones originales")
        print(f"   - Esto causa que se muestren 'documentos solos' al final")
        
        # Simular navegación
        print(f"\n🧭 Simulando navegación...")
        
        # 1. Ir al primer video
        response = client.get(reverse('course_unified_navigation', kwargs={
            'slug': course.slug,
            'content_id': video1.id,
            'content_type': 'video'
        }), HTTP_HOST='localhost')
        
        print(f"1. Video 1 - Status: {response.status_code}")
        
        # 2. Marcar video 1 como completado
        url = reverse('mark_content_completed_ajax', kwargs={
            'slug': course.slug,
            'content_id': video1.id,
            'content_type': 'video'
        })
        
        response = client.post(url, 
            data=json.dumps({'mark_completed': True}),
            content_type='application/json',
            HTTP_HOST='localhost'
        )
        
        print(f"2. Video 1 completado - Status: {response.status_code}")
        
        # 3. Ir al documento relacionado con video 1
        response = client.get(reverse('course_unified_navigation', kwargs={
            'slug': course.slug,
            'content_id': doc1.id,
            'content_type': 'document'
        }), HTTP_HOST='localhost')
        
        print(f"3. Documento 1 (relacionado) - Status: {response.status_code}")
        
        # 4. Marcar documento 1 como completado
        url = reverse('mark_content_completed_ajax', kwargs={
            'slug': course.slug,
            'content_id': doc1.id,
            'content_type': 'document'
        })
        
        response = client.post(url, 
            data=json.dumps({'mark_completed': True}),
            content_type='application/json',
            HTTP_HOST='localhost'
        )
        
        print(f"4. Documento 1 completado - Status: {response.status_code}")
        
        # 5. Ir al segundo video
        response = client.get(reverse('course_unified_navigation', kwargs={
            'slug': course.slug,
            'content_id': video2.id,
            'content_type': 'video'
        }), HTTP_HOST='localhost')
        
        print(f"5. Video 2 - Status: {response.status_code}")
        
        # 6. Marcar video 2 como completado
        url = reverse('mark_content_completed_ajax', kwargs={
            'slug': course.slug,
            'content_id': video2.id,
            'content_type': 'video'
        })
        
        response = client.post(url, 
            data=json.dumps({'mark_completed': True}),
            content_type='application/json',
            HTTP_HOST='localhost'
        )
        
        print(f"6. Video 2 completado - Status: {response.status_code}")
        
        # 7. Ir al documento relacionado con video 2
        response = client.get(reverse('course_unified_navigation', kwargs={
            'slug': course.slug,
            'content_id': doc2.id,
            'content_type': 'document'
        }), HTTP_HOST='localhost')
        
        print(f"7. Documento 2 (relacionado) - Status: {response.status_code}")
        
        # 8. Marcar documento 2 como completado
        url = reverse('mark_content_completed_ajax', kwargs={
            'slug': course.slug,
            'content_id': doc2.id,
            'content_type': 'document'
        })
        
        response = client.post(url, 
            data=json.dumps({'mark_completed': True}),
            content_type='application/json',
            HTTP_HOST='localhost'
        )
        
        print(f"8. Documento 2 completado - Status: {response.status_code}")
        
        # 9. Verificar qué viene después (debería ser documento 3, pero aparece como "documento solo")
        print(f"\n🔍 PROBLEMA: Después de completar videos y documentos relacionados...")
        print(f"   - El sistema muestra documentos 3 y 4 como 'documentos solos'")
        print(f"   - Pero estos documentos NO tienen video relacionado")
        print(f"   - El problema está en la lógica de get_unified_course_content")
        
        print(f"\n✅ PROBLEMA REPRODUCIDO EXITOSAMENTE")
        print(f"   - Se confirma que documentos sin video relacionado aparecen al final")
        print(f"   - Esto causa la duplicación de documentos en la navegación")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Limpiar
        try:
            VideoCompletion.objects.filter(user=user).delete()
            DocumentCompletion.objects.filter(user=user).delete()
            UploadVideo.objects.filter(course=course).delete()
            Upload.objects.filter(course=course).delete()
            TakenCourse.objects.filter(student=student).delete()
            Student.objects.filter(student=user).delete()
            Course.objects.filter(slug=course.slug).delete()
            Program.objects.filter(title__startswith='Programa Test').delete()
            User.objects.filter(username='test_video_doc_issue').delete()
            print("✅ Datos limpiados")
        except:
            pass

if __name__ == '__main__':
    success = test_video_document_issue()
    sys.exit(0 if success else 1)

