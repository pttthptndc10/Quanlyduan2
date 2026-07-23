from django.urls import path
from . import views

urlpatterns = [
    path('', views.root_redirect, name='root'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('api/send-otp/', views.send_otp_view, name='send_otp'),
    path('auth/invite/', views.create_invitation_view, name='create_invitation'),
]
