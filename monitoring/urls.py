from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('dashboard/<str:codigo_lote>/', views.DashboardView.as_view(), name='dashboard'),
    path('camera/<str:codigo_lote>/', views.CameraView.as_view(), name='camera'),
    path('history/<str:codigo_lote>/', views.HistoryView.as_view(), name='history'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    
    # API endpoints locales de lotes
    path('api/lots/', views.LoteListCreateAPIView.as_view(), name='api-lots'),
    path('api/lots/<str:codigo>/', views.LoteDetailAPIView.as_view(), name='api-lot-detail'),
    path('api/lots/<str:codigo>/statistics/', views.LoteStatisticsAPIView.as_view(), name='api-lot-statistics'),
]
