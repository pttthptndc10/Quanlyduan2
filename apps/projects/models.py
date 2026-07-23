"""
Projects Models — Quản lý Dự án nội bộ.
"""
from django.db import models
from django.contrib.auth.models import User

class Project(models.Model):
    STATUS_CHOICES = (
        ('planning', 'Lên kế hoạch'),
        ('in_progress', 'Đang thực hiện'),
        ('review', 'Đang review'),
        ('completed', 'Hoàn thành'),
        ('paused', 'Tạm dừng'),
    )
    PRIORITY_CHOICES = (
        ('low', 'Thấp'),
        ('medium', 'Trung bình'),
        ('high', 'Cao'),
        ('critical', 'Khẩn cấp'),
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    deadline = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ProjectMember(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_memberships')
    role = models.CharField(max_length=20, default='member')

    class Meta:
        unique_together = ('project', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.project.name}"
