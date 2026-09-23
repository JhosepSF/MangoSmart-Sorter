from django.urls import path
from . import views
from hardware import views as hardware_views

urlpatterns = [
    # Endpoints de Clasificación
    path('classifications/capture/', views.ClassificationCaptureAPIView.as_view(), name='api-classification-capture'),
    path('classifications/<int:pk>/', views.ClassificationDetailAPIView.as_view(), name='api-classification-detail'),
    
    # Endpoints de Hardware (de la aplicación hardware)
    path('hardware/test-command/', hardware_views.HardwareTestCommandAPIView.as_view(), name='api-hardware-test'),
    path('hardware/status/', hardware_views.HardwareStatusAPIView.as_view(), name='api-hardware-status'),
    
    # Endpoints de Sistema
    path('system/reset-counters/', hardware_views.ResetCountersAPIView.as_view(), name='api-reset-counters'),
]
