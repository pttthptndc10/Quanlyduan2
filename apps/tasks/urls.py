from django.urls import path
from . import views

urlpatterns = [
    path('', views.tasks_list, name='tasks'),
    path('create/', views.task_create, name='task_create'),
    path('<str:task_id>/', views.task_detail, name='task_detail'),
    path('<str:task_id>/edit/', views.task_edit, name='task_edit'),
    path('<str:task_id>/delete/', views.task_delete, name='task_delete'),
    path('api/update-status/', views.update_task_status, name='update_task_status'),
]
