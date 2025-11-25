from django.urls import path
from . import views

urlpatterns = [
    path("<slug>/quizzes/", views.quiz_list, name="quiz_index"),
    path("progress/", view=views.QuizUserProgressView.as_view(), name="quiz_progress"),
    # path('marking/<int:pk>/', view=QuizMarkingList.as_view(), name='quiz_marking'),
    path("marking_list/", view=views.QuizMarkingList.as_view(), name="quiz_marking"),
    path(
        "marking/<int:pk>/",
        view=views.QuizMarkingDetail.as_view(),
        name="quiz_marking_detail",
    ),
    path("<int:pk>/<slug>/take/", view=views.QuizTake.as_view(), name="quiz_take"),
    path("<slug>/quiz_add/", views.QuizCreateView.as_view(), name="quiz_create"),
    path("<slug>/<int:pk>/add/", views.QuizUpdateView.as_view(), name="quiz_update"),
    path("<slug>/<int:pk>/delete/", views.quiz_delete, name="quiz_delete"),
    path(
        "mc-question/add/<slug>/<int:quiz_id>/",
        views.MCQuestionCreate.as_view(),
        name="mc_create",
    ),
    path('certificado/<int:sitting_id>/', views.generar_certificado, name='generar_certificado'),
    path('descargar-certificados/', views.descargar_tabla_pdf, name='descargar_certificados'),
    path('generar_anexo4/<int:sitting_id>/', views.generar_anexo4, name='generar_anexo4'),
    path('anexo_form/<int:sitting_id>/', views.anexo_form, name='anexo_form'),
    path('verificar-certificado/<str:codigo>/', views.verificar_certificado, name='verificar_certificado'),
    
    # URLs para certificados manuales
    path('certificados-manuales/', views.listar_certificados_manuales, name='listar_certificados_manuales'),
    path('generar-certificado-manual/', views.generar_certificado_manual, name='generar_certificado_manual'),
    path('descargar-certificado-manual/<int:cert_id>/', views.descargar_certificado_manual, name='descargar_certificado_manual'),
    path('editar-certificado-manual/<int:pk>/', views.ManualCertificateUpdateView.as_view(), name='editar_certificado_manual'),
    
    # URL para editar fecha de aprobación (modo libre)
    path('editar-fecha-aprobacion/<int:pk>/', views.SittingDateUpdateView.as_view(), name='editar_fecha_aprobacion'),
   
    # path('mc-question/add/<int:pk>/<quiz_pk>/', MCQuestionCreate.as_view(), name='mc_create'),
    path('certificados-dashboard/', views.CertificadosDashboardView.as_view(), name='certificados_dashboard'),
    path('certificados-dashboard/beneficiarios/', views.BeneficiariosAjaxView.as_view(), name='beneficiarios_ajax'),
    path('certificados-dashboard/filtros/', views.CertificadosFiltrosAjaxView.as_view(), name='certificados_filtros_ajax'),
    path('estadisticas-por-curso-ajax/', views.CertificadosEstadisticasAjaxView.as_view(), name='estadisticas_por_curso_ajax'),
    
    # URLs para Cursos Externos
    path('external-courses/', views.ExternalCourseListView.as_view(), name='external_course_list'),
    path('external-courses/new/', views.ExternalCourseCreateView.as_view(), name='external_course_create'),
    path('external-courses/<int:pk>/edit/', views.ExternalCourseUpdateView.as_view(), name='external_course_update'),
    path('my-external-courses/', views.MyExternalCoursesView.as_view(), name='my_external_courses'),
    path('external-courses/validation/', views.ExternalCourseValidationView.as_view(), name='external_course_validation'),
]
