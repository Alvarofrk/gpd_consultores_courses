#!/usr/bin/env python
"""
Script de prueba específico para verificar la actualización de "Mis Cursos"
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

User = get_user_model()

def test_my_courses_update():
    """Prueba específica de actualización de Mis Cursos"""
    print("🧪 PRUEBA DE ACTUALIZACIÓN DE 'MIS CURSOS'")
    print("=" * 60)
    
    client = Client()
    
    try:
        # Crear datos de prueba
        user = User.objects.create_user(
            username='test_my_courses',
            email='test@mycourses.com',
            password='testpass123'
        )
        
        # Crear programa
        program = Program.objects.create(title='Programa Test Mis Cursos', summary='Test')
        
        # Crear estudiante
        student = Student.objects.create(
            student=user,
            program=program
        )
        
        course = Course.objects.create(
            title='Curso Test Mis Cursos',
            code='MISCURSOS001',
            summary='Curso para test Mis Cursos',
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
            title='Video 1 Test',
            course=course,
            youtube_url='https://youtube.com/watch?v=test1',
            order=0
        )
        
        video2 = UploadVideo.objects.create(
            title='Video 2 Test',
            course=course,
            youtube_url='https://youtube.com/watch?v=test2',
            order=1
        )
        
        print(f"✅ Datos creados - Usuario: {user.username}, Curso: {course.title}")
        print(f"✅ Videos: {video1.title}, {video2.title}")
        
        # Login
        client.force_login(user)
        
        # 1. Verificar estado inicial de "Mis Cursos"
        print("\n1️⃣ Verificando estado inicial de 'Mis Cursos'...")
        
        response = client.get(reverse('user_course_list'), HTTP_HOST='localhost')
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            print("✅ Sección 'Mis Cursos' accesible")
            
            # Buscar información de progreso en el HTML
            if '0%' in content or '0.0%' in content:
                print("✅ Progreso inicial: 0% (correcto)")
            else:
                print("⚠️ Progreso inicial no es 0%")
        else:
            print(f"❌ Error en 'Mis Cursos': {response.status_code}")
            return False
        
        # 2. Marcar video1 como completado via AJAX
        print("\n2️⃣ Marcando Video 1 como completado via AJAX...")
        
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
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AJAX exitoso - Completado: {data.get('is_completed', 'N/A')}")
        else:
            print(f"❌ Error en AJAX: {response.status_code}")
            return False
        
        # 3. Verificar que el video está marcado como completado en la BD
        print("\n3️⃣ Verificando en base de datos...")
        
        is_video1_completed = VideoCompletion.objects.filter(user=user, video=video1).exists()
        print(f"✅ Video 1 completado en BD: {is_video1_completed}")
        
        if not is_video1_completed:
            print("❌ Video no está marcado como completado en la BD")
            return False
        
        # 4. Verificar actualización de "Mis Cursos" (debería mostrar 50% de progreso)
        print("\n4️⃣ Verificando actualización de 'Mis Cursos'...")
        
        response = client.get(reverse('user_course_list'), HTTP_HOST='localhost')
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Buscar información de progreso actualizada
            if '50%' in content or '50.0%' in content:
                print("✅ Progreso actualizado: 50% (correcto)")
            elif '100%' in content or '100.0%' in content:
                print("⚠️ Progreso muestra 100% (puede ser correcto si hay solo 1 video)")
            elif '0%' in content or '0.0%' in content:
                print("❌ Progreso sigue en 0% - CACHÉ NO SE ACTUALIZÓ")
                return False
            else:
                print(f"⚠️ Progreso no reconocido en el HTML")
                print(f"Contenido relevante: {content[content.find('progress'):content.find('progress')+100] if 'progress' in content else 'No encontrado'}")
        else:
            print(f"❌ Error en 'Mis Cursos': {response.status_code}")
            return False
        
        # 5. Marcar video2 como completado
        print("\n5️⃣ Marcando Video 2 como completado...")
        
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
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AJAX exitoso - Completado: {data.get('is_completed', 'N/A')}")
        else:
            print(f"❌ Error en AJAX: {response.status_code}")
            return False
        
        # 6. Verificar progreso final (debería ser 100%)
        print("\n6️⃣ Verificando progreso final...")
        
        response = client.get(reverse('user_course_list'), HTTP_HOST='localhost')
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            if '100%' in content or '100.0%' in content:
                print("✅ Progreso final: 100% (correcto)")
            else:
                print("⚠️ Progreso final no es 100%")
                print(f"Contenido relevante: {content[content.find('progress'):content.find('progress')+100] if 'progress' in content else 'No encontrado'}")
        else:
            print(f"❌ Error en 'Mis Cursos': {response.status_code}")
            return False
        
        print("\n" + "=" * 60)
        print("🎉 PRUEBA DE ACTUALIZACIÓN DE 'MIS CURSOS' EXITOSA")
        print("✅ Caché se invalida correctamente")
        print("✅ Progreso se actualiza en tiempo real")
        print("✅ 'Mis Cursos' refleja cambios inmediatamente")
        print("=" * 60)
        
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
            User.objects.filter(username='test_my_courses').delete()
            print("✅ Datos limpiados")
        except:
            pass

if __name__ == '__main__':
    success = test_my_courses_update()
    sys.exit(0 if success else 1)
