from django.urls import path
from . import views
from pagos.views import CargarConceptosConsultaView

urlpatterns = [
    # 🔄 Redirección intermedia post-login
    path('redireccion/', views.redireccionar_segun_rol, name='redireccion_rol'), # type: ignore
    
    # 🖥️ Menús principales de inicio (Dashboards)
    path('menu-operador/', views.MenuOperadorView.as_view(), name='menu_operador'),
    path('menu-administrador/', views.MenuAdministradorView.as_view(), name='menu_administrador'),
    
    # 👥 Registro de Dueño y 🐾 Mascota (Operador)
    path('nuevo-dueno/', views.DuenoCreateView.as_view(), name='crear_dueño'),
    path('nueva-mascota/', views.MascotaCreateView.as_view(), name='crear_mascota'),
    
    # 📥 Flujo de Ingreso y Espera (Operador manda a Sala de Espera)
    path('nueva-preconsulta/', views.PreConsultaCreateView.as_view(), name='crear_preconsulta'),
    
    # 🩺 Flujo Clínico del Médico (Sala de espera)
    path('sala-espera/', views.ConsultasPendientesListView.as_view(), name='consultas_pendientes'),
    
    # 1️⃣ PASO CLÍNICO: El médico carga peso, diagnóstico, etc.
    path('atender-consulta/<int:pk>/', views.AtenderConsultaView.as_view(), name='cerrar_consulta'), 

    # 2️⃣ PASO FINANCIERO: Redirección inmediata automática post-guardado clínico
    path('atender-consulta/<int:consulta_id>/prefactura/', CargarConceptosConsultaView.as_view(), name='cargar_conceptos_consulta'),

    # Ruta para cancelar una consulta por el médico
    path('cancelar-consulta/<int:pk>/', views.CancelarConsultaView.as_view(), name='cancelar_consulta'),

    path('historial-clinico/', views.HistorialClinicoListView.as_view(), name='historial_clinico'),

    # ALTA DE OPERADORES
    path('operadores/', views.OperadoresListView.as_view(), name='gestion_operadores'),
    path('operadores/nuevo/', views.OperadorCreateView.as_view(), name='alta_operador'),
    path('operadores/cambiar-estado/<int:pk>/', views.CambiarEstadoOperadorView.as_view(), name='cambiar_estado_operador'),

    path('reportes/', views.ReportesEstadisticosView.as_view(), name='reportes_estadisticos'),
]