from django.urls import path
from . import views

urlpatterns = [
    path('', views.projects_list, name='projects'),
    path('<str:project_id>/', views.project_detail, name='project_detail'),
    path('create/', views.project_create, name='project_create'),
    path('<str:project_id>/edit/', views.project_edit, name='project_edit'),
    path('<str:project_id>/delete/', views.project_delete, name='project_delete'),
]
