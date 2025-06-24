# GPD Consultores - Sistema de Gestión de Cursos y Certificaciones

## 📋 Descripción

Sistema de gestión integral para cursos de capacitación y certificaciones profesionales desarrollado en Django. Permite la administración de estudiantes, instructores, cursos, evaluaciones, pagos y generación de certificados.

## 🚀 Características Principales

- **Gestión de Usuarios**: Estudiantes, instructores, padres y jefes de departamento
- **Gestión de Cursos**: Programas, cursos, materiales y videos
- **Sistema de Evaluaciones**: Quizzes, exámenes y seguimiento de progreso
- **Sistema de Pagos**: Integración con múltiples pasarelas de pago
- **Certificados**: Generación automática de certificados de aprobación
- **Multilingüe**: Soporte para español, inglés, francés y ruso
- **Panel de Administración**: Interfaz personalizada con Django Jet
- **Gestión de Cotizaciones**: Sistema completo de cotizaciones para servicios

## 🛠️ Tecnologías Utilizadas

- **Backend**: Django 4.2.10 (LTS)
- **Base de Datos**: PostgreSQL
- **Frontend**: Bootstrap 5, jQuery, FontAwesome
- **Autenticación**: Django Auth con modelo de usuario personalizado
- **Archivos**: WhiteNoise para servir archivos estáticos
- **PDF**: ReportLab para generación de certificados
- **Pagos**: Stripe, PayPal, Coinbase, Paylike
- **Traducciones**: Django Modeltranslation

## 📦 Requisitos del Sistema

- Python 3.9+ (recomendado: Python 3.11 o 3.12 para mejor compatibilidad)
- PostgreSQL 12+
- pip
- virtualenv (recomendado)

## 🔧 Instalación

### 1. Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd gpd_consultores_courses
```

### 2. Crear Entorno Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
# Instalar todas las dependencias
pip install -r requirements.txt
```

**Nota**: Si tienes problemas con Python 3.13, puedes instalar las dependencias una por una:

```bash
# Instalar Pillow primero (versión compatible con Python 3.13)
pip install Pillow==10.4.0

# Luego instalar el resto
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Crear un archivo `.env` en la raíz del proyecto:

```env
# Configuración de Django
SECRET_KEY=tu_clave_secreta_aqui
DEBUG=True

# Configuración de Base de Datos
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=nombre_base_datos
DATABASE_USER=usuario_base_datos
DATABASE_PASSWORD=contraseña_base_datos
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Configuración de Pagos (opcional)
STRIPE_PUBLISHABLE_KEY=tu_stripe_public_key
STRIPE_SECRET_KEY=tu_stripe_secret_key

# Configuración de Email (opcional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_contraseña_app
```

### 5. Configurar Base de Datos

```bash
# Crear base de datos PostgreSQL
createdb nombre_base_datos

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser
```

### 6. Recolectar Archivos Estáticos

```bash
python manage.py collectstatic
```

### 7. Ejecutar el Servidor

```bash
python manage.py runserver
```

El proyecto estará disponible en `http://127.0.0.1:8000/`

## 📁 Estructura del Proyecto

```
gpd_consultores_courses/
├── accounts/                 # Gestión de usuarios y autenticación
├── core/                     # Modelos base y funcionalidades centrales
├── course/                   # Gestión de cursos y programas
├── quiz/                     # Sistema de evaluaciones y quizzes
├── payments/                 # Integración de pasarelas de pago
├── result/                   # Gestión de resultados y certificados
├── search/                   # Funcionalidad de búsqueda
├── config/                   # Configuración de Django
├── templates/                # Plantillas HTML
├── static/                   # Archivos estáticos (CSS, JS, imágenes)
├── media/                    # Archivos subidos por usuarios
├── requirements.txt          # Dependencias del proyecto
└── scripts/                  # Scripts de utilidad
```

## 👥 Tipos de Usuarios

### 1. Superusuario
- Acceso completo al sistema
- Gestión de todos los módulos

### 2. Jefe de Departamento
- Gestión de programas y cursos
- Asignación de instructores
- Creación de cotizaciones

### 3. Instructor
- Gestión de cursos asignados
- Subida de materiales
- Creación de evaluaciones
- Seguimiento de estudiantes

### 4. Estudiante
- Acceso a cursos inscritos
- Realización de evaluaciones
- Visualización de progreso
- Descarga de certificados

### 5. Padre/Tutor
- Seguimiento del progreso de estudiantes
- Acceso limitado a información

## 🎓 Gestión de Cursos

### Programas
- Creación de programas de estudio
- Organización jerárquica de cursos
- Gestión de niveles (Bachelor, Master)

### Cursos
- Creación y edición de cursos
- Asignación de instructores
- Subida de materiales (PDF, videos)
- Configuración de evaluaciones

### Materiales
- Soporte para múltiples formatos
- Organización por curso
- Control de acceso

## 📝 Sistema de Evaluaciones

### Tipos de Preguntas
- **Opción Múltiple**: Preguntas con múltiples opciones
- **Ensayo**: Preguntas de desarrollo

### Características
- Configuración de puntaje mínimo para aprobar
- Múltiples intentos (configurable)
- Orden aleatorio de preguntas
- Explicaciones post-evaluación

### Seguimiento
- Registro de intentos
- Historial de evaluaciones
- Generación automática de certificados

## 💳 Sistema de Pagos

### Pasarelas Soportadas
- **Stripe**: Pagos con tarjeta de crédito
- **PayPal**: Pagos internacionales
- **Coinbase**: Pagos con criptomonedas
- **Paylike**: Pagos alternativos

### Funcionalidades
- Creación de facturas
- Seguimiento de pagos
- Integración con cursos

## 📊 Gestión de Resultados

### Certificados
- Generación automática al aprobar
- Códigos únicos de certificado
- Plantillas personalizables
- Exportación en PDF

### Reportes
- Historial de evaluaciones
- Estadísticas de rendimiento
- Reportes por estudiante/curso

## 🏢 Sistema de Cotizaciones

### Características
- Creación de cotizaciones detalladas
- Gestión de estados (pendiente, aceptado, rechazado)
- Cálculo automático de montos
- Historial de cambios
- Múltiples modalidades de pago

## 🌐 Configuración Multilingüe

El sistema soporta múltiples idiomas:
- Español (predeterminado)
- Inglés
- Francés
- Ruso

### Configuración de Idiomas

```bash
# Compilar archivos de traducción
python manage.py compilemessages

# Crear archivos de traducción
python manage.py makemessages -l es
python manage.py makemessages -l en
python manage.py makemessages -l fr
python manage.py makemessages -l ru
```

## 🚀 Despliegue

### Despliegue Local

```bash
# Configurar para producción
export DEBUG=False
export DJANGO_SETTINGS_MODULE=config.settings

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Aplicar migraciones
python manage.py migrate

# Ejecutar con Gunicorn
gunicorn config.wsgi:application
```

### Despliegue en Google Cloud Platform

El proyecto incluye configuración para GCP:

```bash
# Usar app.yaml para configuración
gcloud app deploy

# Configurar Cloud SQL
gcloud sql connect instance-name
```

### Variables de Entorno para Producción

```env
DEBUG=False
SECRET_KEY=clave_secreta_produccion
DATABASE_URL=postgresql://usuario:contraseña@host:puerto/base_datos
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
```

## 📋 Scripts de Utilidad

### Generación de Datos de Prueba

```bash
# Generar datos de cuentas
python scripts/generate_fake_accounts_data.py

# Generar datos del core
python scripts/generate_fake_core_data.py
```

### Limpieza de Base de Datos

```bash
# Limpiar estudiantes
python clean_students.py

# Limpiar base de datos
python clean_db.py
```

## 🔒 Seguridad

### Configuraciones de Seguridad
- CSRF protection habilitado
- Validación de archivos subidos
- Autenticación requerida para vistas sensibles
- Permisos granulares por tipo de usuario

### Recomendaciones
- Cambiar SECRET_KEY en producción
- Usar HTTPS en producción
- Configurar firewall de base de datos
- Realizar backups regulares

## 🐛 Solución de Problemas

### Errores Comunes

1. **Error de migraciones**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Error de archivos estáticos**
   ```bash
   python manage.py collectstatic --clear
   ```

3. **Error de base de datos**
   - Verificar configuración en `.env`
   - Comprobar conexión a PostgreSQL

4. **Error con Pillow en Python 3.13**
   ```bash
   # Solución 1: Instalar Pillow manualmente primero
   pip install Pillow==10.4.0
   pip install -r requirements.txt
   
   # Solución 2: Usar una versión anterior de Python (3.11 o 3.12)
   ```

5. **Error de dependencias incompatibles**
   ```bash
   # Limpiar cache de pip
   pip cache purge
   
   # Reinstalar dependencias
   pip uninstall -r requirements.txt -y
   pip install -r requirements.txt
   ```

6. **Error de permisos en Windows**
   ```bash
   # Ejecutar PowerShell como administrador
   Set-ExecutionPolicy RemoteSigned
   ```

### Logs
Los logs se encuentran en:
- Django logs: `logs/django.log`
- Error logs: `logs/error.log`

### Compatibilidad de Python

| Versión de Python | Estado | Recomendación |
|-------------------|--------|---------------|
| Python 3.9-3.10   | ✅ Compatible | Recomendado |
| Python 3.11-3.12  | ✅ Compatible | Óptimo |
| Python 3.13       | ⚠️ Compatible con limitaciones | Instalar Pillow manualmente |

## 📞 Soporte

Para soporte técnico o consultas:
- Email: soporte@gpdconsultores.com
- Documentación: [URL de documentación]
- Issues: [URL del repositorio de issues]

## 📄 Licencia

Este proyecto está bajo la licencia [TIPO DE LICENCIA]. Ver el archivo `LICENSE` para más detalles.

## 🤝 Contribución

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

---

**Desarrollado por GPD Consultores** - Sistema de Gestión de Cursos y Certificaciones
