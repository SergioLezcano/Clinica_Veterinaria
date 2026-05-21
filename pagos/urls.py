from django.urls import path
from . import views

urlpatterns = [
    path('pendientes/', views.FacturasPendientesListView.as_view(), name='facturas_pendientes'),
    path('cobrar/<int:pk>/', views.ProcesarPagoView.as_view(), name='procesar_pago'),
    path('prefactura/<int:consulta_id>/', views.CargarConceptosConsultaView.as_view(), name='cargar_conceptos_consulta'),
]