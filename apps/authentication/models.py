"""
Authentication Models — Quản lý tài khoản, Hồ sơ và Lời mời Whitelist.
"""
from django.db import models
from django.contrib.auth.models import User
import uuid

class Profile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Quản trị viên'),
        ('leader', 'Trưởng nhóm'),
        ('member', 'Thành viên'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    department = models.CharField(max_length=150, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default='active')

    def __str__(self):
        return f"{self.full_name} ({self.role})"


class Invitation(models.Model):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150, blank=True, null=True)
    role = models.CharField(max_length=20, default='member')
    token = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invite for {self.email} ({self.role})"


class OTPCode(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP {self.code} for {self.email}"
