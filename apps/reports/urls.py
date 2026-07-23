"""
Reports URLs — Báo cáo, Quản lý Gom hàng & Xuất file Excel (.xlsx / .csv).
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_view, name='reports'),
    path('batch/create/', views.create_batch, name='create_batch'),
    path('batch/<str:batch_id>/export/', views.export_batch_excel, name='export_batch_excel'),
    path('export/tasks/', views.export_tasks_csv, name='export_tasks'),
]
