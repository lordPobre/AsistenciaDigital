from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('marcar/', views.registrar_marca, name='registrar_marca'),
    path('mis-marcas/', views.mis_marcas, name='mis_marcas'),
    path('solicitudes/responder/<int:solicitud_id>/<str:accion>/', views.responder_solicitud, name='responder_solicitud'),
    path('panel-empresa/', views.panel_empresa, name='panel_empresa'),
    # path('fiscalizacion/', views.panel_fiscalizador_dt, name='panel_fiscalizador'),
    path('rrhh/panel/', views.panel_rrhh, name='panel_rrhh'),
    path('reportes/fiscalizacion/', views.exportar_reporte_fiscalizacion, name='reporte_fiscalizacion'),
    path('reportes/remuneraciones/', views.exportar_reporte_remuneraciones, name='reporte_remuneraciones'),
    path('fiscalizacion-dt/', views.panel_fiscalizador, name='panel_fiscalizador'),
    path('fiscalizacion/exportar-excel/', views.exportar_reporte_fiscalizacion, name='exportar_reporte_fiscalizacion'),
    path('exportar-excel/', views.exportar_excel_empresa, name='exportar_excel_empresa'),
    path('exportar-clima/', views.exportar_clima_laboral, name='exportar_clima'),
    path('descargar-pdf/', views.generar_pdf, name='reporte_pdf'),
    path('privacidad/', views.privacidad, name='privacidad'),
    path('rrhh/importar-nomina/', views.importar_nomina, name='importar_nomina'),
    path('mis-vacaciones/', views.mis_vacaciones, name='mis_vacaciones'),
    path('mis-dias-administrativos/', views.mis_dias_administrativos, name='mis_dias_administrativos'),
    path('gestionar-dia/<int:solicitud_id>/<str:accion>/', views.gestionar_dia_administrativo, name='gestionar_dia_administrativo'),
    path('rrhh/gestion-ausencias/', views.gestionar_ausencias, name='gestionar_ausencias'),
    path('vacacion/aprobar/<int:id_vacacion>/<str:estado>/', views.aprobar_vacacion, name='aprobar_vacacion'),
    path('api/mejorar-texto/', views.mejorar_justificacion_ia, name='mejorar_texto_ia'),
    path('solicitudes/crear/', views.crear_solicitud_trabajador, name='crear_solicitud_trabajador'),
    path('cambiar-clave/', views.cambiar_password_obligatorio, name='cambiar_password_obligatorio'),
    path('ayuda/', views.manual_ayuda, name='manual_ayuda'),
]