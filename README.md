# 🎓 Proyecto Educativo Seguridad TECK Perú - by AFCR

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/Django-4.2.10-green.svg)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)](https://www.postgresql.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.2-purple.svg)](https://getbootstrap.com/)
[![License](https://img.shields.io/badge/License-Propietaria-red.svg)](LICENSE.md)

**Desarrollado por:** Alvaro Franco Cerna Ramos  
**En colaboración con:** G.P.D. CONSULTORES S.A.C.

## 📋 Descripción

Este repositorio contiene el código fuente de la **plataforma educativa** desarrollada por **Alvaro Franco Cerna Ramos** para el proyecto TECK, en colaboración con **G.P.D. CONSULTORES S.A.C.**

Sistema de capacitación online para cumplimiento de formación interna en seguridad por parte de la empresa TECK. Permite la administración completa de cursos de capacitación, gestión de estudiantes, generación automática de certificados, sistema de pagos múltiples y seguimiento de resultados.

## ✨ Características Principales

### 🎯 **Gestión de Usuarios**
- **Sistema de roles**: Administradores, Docentes, Estudiantes
- **Autenticación personalizada** con modelo de usuario extendido
- **Gestión de perfiles** con información detallada
- **Sistema de permisos** granular por rol

### 📚 **Gestión de Cursos**
- **Creación y administración** de cursos y programas
- **Asignación de docentes** a cursos específicos
- **Sistema de inscripciones** y matrículas
- **Gestión de contenido**: archivos PDF, videos, documentación
- **Seguimiento de progreso** de estudiantes

### 🧪 **Sistema de Evaluaciones**
- **Creación de exámenes** con preguntas múltiples y ensayos
- **Configuración de parámetros**: tiempo límite, intentos, nota mínima
- **Evaluación automática** de respuestas
- **Sistema de calificaciones** con diferentes componentes

### 🏆 **Certificados Profesionales**
- **Generación automática** de certificados al aprobar exámenes
- **Certificados manuales** para casos especiales
- **Códigos únicos** de verificación con QR
- **Plantillas personalizadas** por tipo de curso
- **Verificación online** de autenticidad

### 💳 **Sistema de Pagos**
- **Múltiples pasarelas**: Stripe, PayPal, Coinbase, Paylike
- **Gestión de facturas** y transacciones
- **Seguimiento de pagos** y estados
- **Integración completa** con el sistema

### 📊 **Reportes y Analytics**
- **Dashboard administrativo** con métricas clave
- **Reportes de resultados** por estudiante y curso
- **Exportación a PDF** de certificados y reportes
- **Estadísticas de rendimiento** académico

### 🌐 **Características Técnicas**
- **Interfaz responsiva** con Bootstrap 5
- **Soporte multilingüe** (Español, Inglés, Francés, Ruso)
- **API REST** para integraciones externas
- **Sistema de búsqueda** avanzado
- **Paginación** y filtros dinámicos

## 🏗️ Arquitectura del Sistema

### **Aplicaciones Django**

| Aplicación | Descripción |
|------------|-------------|
| **accounts** | Gestión de usuarios, autenticación y perfiles |
| **course** | Administración de cursos, programas y contenido |
| **quiz** | Sistema de exámenes y certificaciones |
| **result** | Gestión de calificaciones y resultados |
| **payments** | Sistema de pagos y facturación |
| **core** | Funcionalidades centrales y cotizaciones |
| **search** | Motor de búsqueda global |

### **Tecnologías Utilizadas**

- **Backend**: Django 4.2.10 (LTS)
- **Base de Datos**: PostgreSQL
- **Frontend**: Bootstrap 5, jQuery, FontAwesome
- **Panel Admin**: Django Jet Reboot
- **Archivos**: WhiteNoise para archivos estáticos
- **PDF**: ReportLab para generación de certificados
- **Pagos**: Stripe, PayPal, Coinbase, Paylike
- **Traducciones**: Django Modeltranslation

## 🚀 Instalación

### **Prerrequisitos**

- Python 3.11 o superior
- PostgreSQL 13 o superior
- pip (gestor de paquetes de Python)
- Git

### **1. Clonar el Repositorio**

```bash
git clone <url-del-repositorio>
cd gpd_consultores_courses
```

### **2. Crear Entorno Virtual**

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows
```

### **3. Instalar Dependencias**

```bash
# Instalar Pillow primero (para Python 3.13+)
pip install Pillow==10.4.0

# Instalar el resto de dependencias
pip install -r requirements.txt
```

### **4. Configurar Base de Datos**

```bash
# Crear base de datos PostgreSQL
createdb gpd_consultores_db

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser
```

### **5. Configurar Variables de Entorno**

Crear archivo `.env` en la raíz del proyecto:

```env
# Configuración de Django
SECRET_KEY=tu_clave_secreta_muy_larga_y_compleja_aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de Datos
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=gpd_consultores_db
DATABASE_USER=tu_usuario
DATABASE_PASSWORD=tu_contraseña
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Email (Gmail)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_contraseña_de_aplicacion
EMAIL_FROM_ADDRESS=tu_email@gmail.com

# Pagos (Stripe)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# Prefijos de ID
STUDENT_ID_PREFIX=ugr
LECTURER_ID_PREFIX=lec
```

### **6. Recolectar Archivos Estáticos**

```bash
python manage.py collectstatic
```

### **7. Ejecutar el Servidor**

```bash
python manage.py runserver
```

Acceder a: http://127.0.0.1:8000

## 📖 Guía de Uso

### **Administradores**

1. **Gestión de Usuarios**
   - Crear y gestionar cuentas de docentes y estudiantes
   - Asignar roles y permisos
   - Administrar perfiles de usuario

2. **Gestión de Cursos**
   - Crear programas y cursos
   - Asignar docentes a cursos
   - Gestionar contenido multimedia

3. **Sistema de Certificaciones**
   - Configurar parámetros de exámenes
   - Generar certificados manuales
   - Verificar autenticidad de certificados

4. **Reportes y Analytics**
   - Acceder al dashboard administrativo
   - Generar reportes de rendimiento
   - Monitorear métricas del sistema

### **Docentes**

1. **Gestión de Cursos Asignados**
   - Ver cursos asignados
   - Subir contenido (PDFs, videos)
   - Gestionar inscripciones

2. **Sistema de Evaluaciones**
   - Crear exámenes y preguntas
   - Configurar parámetros de evaluación
   - Revisar resultados de estudiantes

3. **Calificaciones**
   - Ingresar calificaciones por componente
   - Generar reportes de rendimiento
   - Seguimiento de progreso estudiantil

### **Estudiantes**

1. **Inscripción a Cursos**
   - Ver cursos disponibles
   - Inscribirse en cursos
   - Acceder a contenido multimedia

2. **Evaluaciones**
   - Tomar exámenes en línea
   - Ver resultados y retroalimentación
   - Descargar certificados aprobados

3. **Seguimiento Académico**
   - Ver calificaciones y progreso
   - Acceder a historial de certificados
   - Descargar reportes consolidados

## 🔧 Configuración Avanzada

### **Configuración de Pagos**

#### **Stripe**
```python
# settings.py
STRIPE_SECRET_KEY = 'sk_test_...'
STRIPE_PUBLISHABLE_KEY = 'pk_test_...'
```

#### **PayPal**
```python
# Configurar en templates/payments/payment_gateways.html
PAYPAL_CLIENT_ID = 'tu_client_id'
```

### **Configuración de Email**

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu_email@gmail.com'
EMAIL_HOST_PASSWORD = 'tu_contraseña_de_aplicacion'
```

### **Configuración de Certificados**

Los certificados se generan automáticamente cuando un estudiante aprueba un examen con 80% o más. Las plantillas se encuentran en `static/pdfs/` y deben seguir el formato `{código_curso}.pdf`.

## 🚀 Despliegue

### **Render (Recomendado)**

1. **Conectar repositorio** a Render
2. **Configurar variables de entorno** en el dashboard
3. **Especificar comando de build**: `./build.sh`
4. **Configurar base de datos** PostgreSQL

### **Google Cloud Platform**

1. **Configurar Cloud SQL** para PostgreSQL
2. **Desplegar con Cloud Run** usando el Dockerfile
3. **Configurar variables de entorno** en Cloud Run

### **Docker**

```bash
# Construir imagen
docker build -t gpd-consultores .

# Ejecutar contenedor
docker run -p 8080:8080 gpd-consultores
```

## 📊 Estructura de Base de Datos

### **Modelos Principales**

- **User**: Usuarios del sistema (estudiantes, docentes, administradores)
- **Course**: Cursos y programas educativos
- **Quiz**: Exámenes y evaluaciones
- **Sitting**: Intentos de examen y resultados
- **Certificate**: Certificados generados
- **Payment**: Transacciones de pago
- **Cotizacion**: Sistema de cotizaciones

## 🔒 Seguridad

### **Configuraciones Implementadas**

- **CSRF Protection**: Habilitado en todas las vistas
- **XSS Protection**: Headers de seguridad configurados
- **SQL Injection**: ORM de Django con parámetros seguros
- **File Upload Security**: Validación de tipos y tamaños
- **Authentication**: Sistema robusto de autenticación

### **Variables de Entorno Críticas**

```env
SECRET_KEY=clave_secreta_muy_larga_y_compleja
DEBUG=False  # En producción
ALLOWED_HOSTS=tu-dominio.com
DATABASE_PASSWORD=contraseña_fuerte
```

## 🧪 Testing

```bash
# Ejecutar tests
python manage.py test

# Tests específicos
python manage.py test accounts
python manage.py test quiz
python manage.py test course
```

## 📝 Scripts de Datos

### **Generar Datos de Prueba**

```bash
# Generar usuarios de prueba
python scripts/generate_fake_accounts_data.py

# Generar datos del sistema
python scripts/generate_fake_core_data.py
```

## 🔄 Mantenimiento

### **Backup de Base de Datos**

```bash
# Backup
pg_dump gpd_consultores_db > backup.sql

# Restore
psql gpd_consultores_db < backup.sql
```

### **Actualizaciones**

```bash
# Actualizar dependencias
pip install -r requirements.txt --upgrade

# Aplicar migraciones
python manage.py migrate

# Recolectar estáticos
python manage.py collectstatic
```

## 📞 Soporte

### **Contacto**
- **Email**: alvaro.cerna.fr@gmail.com
- **Documentación**: [Wiki del proyecto]
- **Issues**: [GitHub Issues]

### **Comunidad**
- **Foro**: [Foro de la comunidad]
- **Discord**: [Servidor de Discord]

## 🔐 Licencia de Uso Limitada

Este software ha sido entregado bajo **licencia de uso limitada** a **G.P.D. CONSULTORES S.A.C.** exclusivamente para:

1. **El proyecto educativo de seguridad con TECK Perú**
2. **La gestión interna educativa de GPD CONSULTORES**

### ⚠️ Limitaciones de esta licencia:

- **Uso restringido** a los fines acordados
- **Prohibida su venta, redistribución o adaptación externa**
- **No implica cesión de propiedad intelectual**

**Todos los derechos reservados** conforme a la Ley sobre el Derecho de Autor del Perú (D.L. N.º 822).

Ver el archivo `LICENSE.md` para detalles completos.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 🙏 Agradecimientos

- **Django Community** por el framework
- **Bootstrap** por el diseño responsivo
- **FontAwesome** por los iconos
- **ReportLab** por la generación de PDFs
- **Stripe** por la integración de pagos

---

**Desarrollado por Alvaro Franco Cerna Ramos**


