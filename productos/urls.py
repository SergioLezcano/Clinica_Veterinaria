from django.urls import path
from . import views

urlpatterns = [
    # 📦 Catálogo y Control de Inventario
    path('', views.CatalogoProductosView.as_view(), name='catalogo_productos'),
    path('nuevo/', views.ProductoCreateView.as_view(), name='crear_producto'),
    path('<int:pk>/editar/', views.ProductoUpdateView.as_view(), name='editar_producto'),
    path('<int:pk>/ajustar-stock/', views.AjustarStockView.as_view(), name='ajustar_stock_producto'),
    path('<int:pk>/cambiar-estado/', views.CambiarEstadoProductoView.as_view(), name='cambiar_estado_producto'),
]
