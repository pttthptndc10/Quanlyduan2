"""
Members Views — Danh sách và hồ sơ thành viên với Django ORM.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from apps.authentication.models import Profile
from apps.tasks.models import Task
from apps.projects.models import Project
from core.utils import get_user_from_session


def members_list(request):
    user = get_user_from_session(request)
    profiles = Profile.objects.select_related('user').all().order_by('full_name')

    member_list = []
    for p in profiles:
        member_list.append({
            'id': p.user.id,
            'full_name': p.full_name,
            'role': p.role,
            'department': p.department or 'Nội bộ',
            'email': p.user.email,
            'status': p.status,
        })

    return render(request, 'members/list.html', {'members': member_list, 'user': user})


def member_detail(request, member_id):
    user = get_user_from_session(request)
    try:
        u = User.objects.select_related('profile').get(id=member_id)
    except User.DoesNotExist:
        return redirect('/members/')

    profile = u.profile
    tasks = Task.objects.filter(assignee=u).select_related('project').order_by('-created_at')[:10]
    projects = Project.objects.filter(members__user=u)

    task_list = [
        {
            'id': t.id, 'title': t.title, 'status': t.status,
            'priority': t.priority,
            'deadline': t.deadline.isoformat() if t.deadline else None,
            'projects': {'name': t.project.name} if t.project else None,
        }
        for t in tasks
    ]

    project_list = [
        {'id': p.id, 'name': p.name, 'status': p.status}
        for p in projects
    ]

    return render(request, 'members/detail.html', {
        'member': {
            'id': u.id,
            'full_name': profile.full_name,
            'role': profile.role,
            'department': profile.department or 'Nội bộ',
            'email': u.email,
            'bio': profile.bio or '',
        },
        'tasks': task_list,
        'projects': project_list,
        'user': user,
    })
