"""
Dashboard Views — Trang tổng quan với Django ORM.
"""

from datetime import date
from django.shortcuts import render
from apps.projects.models import Project
from apps.tasks.models import Task
from apps.authentication.models import Profile
from core.utils import get_user_from_session, TASK_STATUS_LABELS


def dashboard_view(request):
    user = get_user_from_session(request)
    user_id = user['id']
    today = date.today().isoformat()

    projects = Project.objects.all().order_by('-updated_at')
    tasks = Task.objects.all().select_related('project', 'assignee__profile')

    my_tasks = tasks.filter(assignee_id=user_id).order_by('-created_at')[:5]

    total_projects = projects.count()
    active_projects = projects.filter(status='in_progress').count()
    total_tasks = tasks.count()
    done_tasks = tasks.filter(status='done').count()
    overdue_tasks = sum(1 for t in tasks if t.deadline and t.deadline.isoformat() < today and t.status not in ('done', 'cancelled'))
    blocked_tasks = tasks.filter(status='blocked').count()

    total_members = Profile.objects.filter(status='active').count()

    # Format my tasks for template
    my_tasks_data = [
        {
            'id': t.id,
            'title': t.title,
            'status': t.status,
            'priority': t.priority,
            'progress': t.progress,
            'deadline': t.deadline.isoformat() if t.deadline else None,
            'projects': {'name': t.project.name} if t.project else None,
        }
        for t in my_tasks
    ]

    # Format recent projects for template
    recent_projects_data = []
    for p in projects[:6]:
        ptasks = p.tasks.all()
        pdone = ptasks.filter(status='done').count()
        ptotal = ptasks.count()
        recent_projects_data.append({
            'id': p.id,
            'name': p.name,
            'status': p.status,
            'done_count': pdone,
            'task_count': ptotal,
        })

    stats = {
        'total_projects': total_projects,
        'active_projects': active_projects,
        'total_tasks': total_tasks,
        'done_tasks': done_tasks,
        'overdue_tasks': overdue_tasks,
        'blocked_tasks': blocked_tasks,
        'total_members': total_members,
    }

    return render(request, 'dashboard/dashboard.html', {
        'stats': stats,
        'my_tasks': my_tasks_data,
        'recent_projects': recent_projects_data,
        'user': user,
        'today': today,
        'status_labels': TASK_STATUS_LABELS,
    })
