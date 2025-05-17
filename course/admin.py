from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.models import Group
from .models import Program, Course, CourseAllocation, Upload, UploadVideo
from modeltranslation.admin import TranslationAdmin

class CourseInline(admin.StackedInline):
    model = Course
    extra = 1
    fields = ('title', 'code', 'level', 'year', 'semester', 'is_active')

class ProgramAdmin(TranslationAdmin):
    list_display = ['title', 'summary', 'get_courses_count']
    search_fields = ['title', 'summary']
    inlines = [CourseInline]
    
    def get_courses_count(self, obj):
        return obj.course_set.count()
    get_courses_count.short_description = "Número de Cursos"

class CourseAdmin(TranslationAdmin):
    list_display = [
        'title',
        'code',
        'program',
        'level',
        'year',
        'semester',
        'is_active',
        'get_students_count'
    ]
    list_filter = ['program', 'level', 'year', 'semester', 'is_active']
    search_fields = ['title', 'code', 'program__title']
    
    def get_students_count(self, obj):
        students = obj.program.student_set.count()
        return format_html(
            '<span style="color: blue;">{} estudiantes</span>',
            students
        )
    get_students_count.short_description = "Estudiantes Inscritos"

class CourseAllocationAdmin(admin.ModelAdmin):
    list_display = ['lecturer', 'get_courses', 'session']
    search_fields = ['lecturer__username', 'lecturer__first_name', 'lecturer__last_name']
    filter_horizontal = ['courses']
    
    def get_courses(self, obj):
        return format_html(
            '<br>'.join([f'{course.title}' for course in obj.courses.all()])
        )
    get_courses.short_description = "Cursos Asignados"

class UploadAdmin(TranslationAdmin):
    list_display = ['title', 'course', 'get_file_type', 'upload_time']
    list_filter = ['course', 'upload_time']
    search_fields = ['title', 'course__title']
    
    def get_file_type(self, obj):
        return obj.get_extension_short()
    get_file_type.short_description = "Tipo de Archivo"

class UploadVideoAdmin(TranslationAdmin):
    list_display = ['title', 'course', 'get_vimeo_url', 'timestamp']
    list_filter = ['course', 'timestamp']
    search_fields = ['title', 'course__title']
    
    def get_vimeo_url(self, obj):
        if obj.vimeo_url:
            return format_html(
                '<a href="{}" target="_blank">Ver Video</a>',
                obj.vimeo_url
            )
        return "-"
    get_vimeo_url.short_description = "Enlace del Video"

admin.site.register(Program, ProgramAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(CourseAllocation, CourseAllocationAdmin)
admin.site.register(Upload, UploadAdmin)
admin.site.register(UploadVideo, UploadVideoAdmin)
