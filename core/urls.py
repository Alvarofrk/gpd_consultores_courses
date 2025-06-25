from django.urls import path

from .views import (
    home_view,
    post_add,
    edit_post,
    delete_post,
    session_list_view,
    session_add_view,
    session_update_view,
    session_delete_view,
    semester_list_view,
    semester_add_view,
    semester_update_view,
    semester_delete_view,
    dashboard_view,
    cotizaciones_list_view,
    cotizacion_add_view,
    cotizacion_detail_view,
    cotizacion_update_view,
    cotizacion_delete_view,
    cotizacion_change_status_view,
    cotizacion_download_pdf,
    generate_qr_view,
)


urlpatterns = [
    # Accounts url
    path("", home_view, name="home"),
    path("add_item/", post_add, name="add_item"),
    path("item/<int:pk>/edit/", edit_post, name="edit_post"),
    path("item/<int:pk>/delete/", delete_post, name="delete_post"),
    path("session/", session_list_view, name="session_list"),
    path("session/add/", session_add_view, name="add_session"),
    path("session/<int:pk>/edit/", session_update_view, name="edit_session"),
    path("session/<int:pk>/delete/", session_delete_view, name="delete_session"),
    path("semester/", semester_list_view, name="semester_list"),
    path("semester/add/", semester_add_view, name="add_semester"),
    path("semester/<int:pk>/edit/", semester_update_view, name="edit_semester"),
    path("semester/<int:pk>/delete/", semester_delete_view, name="delete_semester"),
    path("dashboard/", dashboard_view, name="dashboard"),
    
    # Cotizaciones URLs
    path("cotizaciones/", cotizaciones_list_view, name="cotizaciones_list"),
    path("cotizaciones/add/", cotizacion_add_view, name="cotizacion_add"),
    path("cotizaciones/<int:pk>/", cotizacion_detail_view, name="cotizacion_detail"),
    path("cotizaciones/<int:pk>/update/", cotizacion_update_view, name="cotizacion_update"),
    path("cotizaciones/<int:pk>/delete/", cotizacion_delete_view, name="cotizacion_delete"),
    path("cotizaciones/<int:pk>/change-status/", cotizacion_change_status_view, name="cotizacion_change_status"),
    path("cotizaciones/<int:pk>/download-pdf/", cotizacion_download_pdf, name="cotizacion_download_pdf"),
    path("generate-qr/", generate_qr_view, name="generate_qr"),
]
