from django.urls import path
from . import views

urlpatterns = [
    path('', views.members_list, name='members'),
    path('<str:member_id>/', views.member_detail, name='member_detail'),
]
