"""
Tasks Models — Quản lý Công việc (Kanban & Task items).
"""
from django.db import models
from django.contrib.auth.models import User
from apps.projects.models import Project

class Task(models.Model):
    STATUS_CHOICES = (
        ('todo', 'Việc cần làm'),
        ('doing', 'Đang làm'),
        ('review', 'Review'),
        ('done', 'Xong'),
        ('blocked', 'Bị chặn'),
        ('cancelled', 'Đã hủy'),
    )
    PRIORITY_CHOICES = (
        ('low', 'Thấp'),
        ('medium', 'Trung bình'),
        ('high', 'Cao'),
        ('critical', 'Khẩn cấp'),
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    deadline = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    progress = models.IntegerField(default=0)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
