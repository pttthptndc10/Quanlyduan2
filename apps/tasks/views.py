"""
Task Views — Quản lý công việc với Django ORM.
"""

import json
from datetime import date
from django.shortcuts import render, redirect
from django.http import JsonResponse
from apps.tasks.models import Task
from apps.projects.models import Project
from django.contrib.auth.models import User
from core.utils import get_user_from_session, TASK_STATUS_LABELS


def tasks_list(request):
    user = get_user_from_session(request)
    tasks = Task.objects.all().select_related('project', 'assignee__profile').order_by('-created_at')

    task_list = []
    for t in tasks:
        assignee_name = t.assignee.profile.full_name if (t.assignee and hasattr(t.assignee, 'profile')) else (t.assignee.email if t.assignee else '—')
        task_list.append({
            'id': t.id,
            'title': t.title,
            'description': t.description,
            'status': t.status,
            'priority': t.priority,
            'progress': t.progress,
            'deadline': t.deadline.isoformat() if t.deadline else None,
            'projects': {'name': t.project.name} if t.project else None,
            'profiles': {'full_name': assignee_name},
        })

    return render(request, 'tasks/list.html', {
        'tasks': task_list,
        'user': user,
        'today': date.today().isoformat(),
        'status_labels': TASK_STATUS_LABELS,
    })


def task_detail(request, task_id):
    user = get_user_from_session(request)
    try:
        t = Task.objects.select_related('project', 'assignee__profile').get(id=task_id)
    except Task.DoesNotExist:
        return redirect('/tasks/')

    assignee_name = t.assignee.profile.full_name if (t.assignee and hasattr(t.assignee, 'profile')) else (t.assignee.email if t.assignee else '—')

    return render(request, 'tasks/detail.html', {
        'task': {
            'id': t.id,
            'title': t.title,
            'description': t.description,
            'status': t.status,
            'priority': t.priority,
            'progress': t.progress,
            'deadline': t.deadline.isoformat() if t.deadline else None,
            'projects': {'name': t.project.name, 'id': t.project.id} if t.project else None,
            'profiles': {'full_name': assignee_name},
        },
        'user': user
    })


def task_create(request):
    user = get_user_from_session(request)
    projects = Project.objects.all()
    members = User.objects.all().select_related('profile')

    member_list = [
        {'id': m.id, 'full_name': m.profile.full_name if hasattr(m, 'profile') else m.email}
        for m in members
    ]

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        desc = request.POST.get('description', '').strip()
        proj_id = request.POST.get('project_id') or None
        ass_id = request.POST.get('assignee_id') or None
        dl = request.POST.get('deadline') or None
        st = request.POST.get('status', 'todo')
        pr = request.POST.get('priority', 'medium')

        if not title:
            return render(request, 'tasks/form.html', {
                'error': 'Tiêu đề không được trống',
                'projects': projects, 'members': member_list,
                'user': user, 'action': 'Tạo công việc'
            })

        project = Project.objects.get(id=proj_id) if proj_id else None
        assignee = User.objects.get(id=ass_id) if ass_id else None
        creator = User.objects.get(id=user['id'])

        Task.objects.create(
            title=title, description=desc, project=project,
            assignee=assignee, deadline=dl, status=st,
            priority=pr, created_by=creator
        )
        return redirect('/tasks/')

    return render(request, 'tasks/form.html', {
        'projects': projects, 'members': member_list,
        'user': user, 'action': 'Tạo công việc'
    })


def task_edit(request, task_id):
    user = get_user_from_session(request)
    try:
        t = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return redirect('/tasks/')

    projects = Project.objects.all()
    members = User.objects.all().select_related('profile')

    member_list = [
        {'id': m.id, 'full_name': m.profile.full_name if hasattr(m, 'profile') else m.email}
        for m in members
    ]

    if request.method == 'POST':
        t.title = request.POST.get('title', '').strip()
        t.description = request.POST.get('description', '').strip()
        proj_id = request.POST.get('project_id') or None
        ass_id = request.POST.get('assignee_id') or None
        t.project = Project.objects.get(id=proj_id) if proj_id else None
        t.assignee = User.objects.get(id=ass_id) if ass_id else None
        t.deadline = request.POST.get('deadline') or None
        t.status = request.POST.get('status', 'todo')
        t.priority = request.POST.get('priority', 'medium')
        t.progress = int(request.POST.get('progress', 0))
        t.save()
        return redirect(f'/tasks/{t.id}/')

    return render(request, 'tasks/form.html', {
        'task': {
            'id': t.id, 'title': t.title, 'description': t.description,
            'project_id': t.project.id if t.project else None,
            'assignee_id': t.assignee.id if t.assignee else None,
            'deadline': t.deadline.isoformat() if t.deadline else None,
            'status': t.status, 'priority': t.priority, 'progress': t.progress
        },
        'projects': projects, 'members': member_list,
        'user': user, 'action': 'Chỉnh sửa công việc'
    })


def task_delete(request, task_id):
    if request.method == 'POST':
        Task.objects.filter(id=task_id).delete()
    return redirect('/tasks/')


def update_task_status(request):
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)
    try:
        data = json.loads(request.body)
        t = Task.objects.get(id=data['task_id'])
        t.status = data['status']
        t.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
