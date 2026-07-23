"""
Reports Models — Phiên gom linh kiện & File Excel tổng hợp.
"""
from django.db import models
from django.contrib.auth.models import User
from apps.projects.models import Project

class ComponentBatch(models.Model):
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, default='active')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ComponentFile(models.Model):
    batch = models.ForeignKey(ComponentBatch, on_delete=models.CASCADE, related_name='files')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    content = models.JSONField(default=list)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File in {self.batch.name}"
