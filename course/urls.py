from django.urls import path
from . import views

urlpatterns = [
    # Program URLs
    path("", views.ProgramFilterView.as_view(), name="programs"),
    path("<int:pk>/detail/", views.program_detail, name="program_detail"),
    path("add/", views.program_add, name="add_program"),
    path("<int:pk>/edit/", views.program_edit, name="edit_program"),
    path("<int:pk>/delete/", views.program_delete, name="program_delete"),
    
    # Course URLs
    path("course/<slug>/detail/", views.course_single, name="course_detail"),
    path("<int:pk>/course/add/", views.course_add, name="course_add"),
    path("course/<slug>/edit/", views.course_edit, name="edit_course"),
    path("course/delete/<slug>/", views.course_delete, name="delete_course"),
    
    # Course Allocation URLs
    path("course/assign/", views.CourseAllocationFormView.as_view(), name="course_allocation"),
    path("course/allocated/", views.CourseAllocationFilterView.as_view(), name="course_allocation_view"),
    path("allocated_course/<int:pk>/edit/", views.edit_allocated_course, name="edit_allocated_course"),
    path("course/<int:pk>/deallocate/", views.deallocate_course, name="course_deallocate"),
    
    # File Uploads URLs
    path("course/<slug>/documentations/upload/", views.handle_file_upload, name="upload_file_view"),
    path("course/<slug>/documentations/<int:file_id>/edit/", views.handle_file_edit, name="upload_file_edit"),
    path("course/<slug>/documentations/<int:file_id>/delete/", views.handle_file_delete, name="upload_file_delete"),
    
    # Video Uploads URLs
    path("course/<slug>/video_tutorials/upload/", views.handle_video_upload, name="upload_video"),
    path("course/<slug>/video_tutorials/<video_slug>/detail/", views.handle_video_single, name="video_single"),
    path("course/<slug>/video_tutorials/<video_slug>/edit/", views.handle_video_edit, name="upload_video_edit"),
    path("course/<slug>/video_tutorials/<video_slug>/delete/", views.handle_video_delete, name="upload_video_delete"),
    
    # Video Navigation URLs
    path(
        "course/<slug>/video_tutorials/<int:video_id>/navigate/",
        views.course_video_navigation,
        name="course_video_navigation"
    ),
    path(
        "course/<slug>/video_tutorials/navigate/",
        views.course_video_navigation,
        name="course_video_navigation_first"
    ),
    
    # Course Registration URLs
    path("course/registration/", views.course_registration, name="course_registration"),
    path("course/drop/", views.course_drop, name="course_drop"),
    path("my_courses/", views.user_course_list, name="user_course_list"),

    path("my_courses/pdf/", views.download_courses_pdf, name="download_courses_pdf"),

    path('video/<int:video_id>/update_order/', views.update_video_order, name='update_video_order'),

    path('document/<int:document_id>/view/', views.PDFViewerView.as_view(), name='view_pdf'),
    path('document/<int:document_id>/download/', views.PDFDownloadView.as_view(), name='download_pdf'),
]
