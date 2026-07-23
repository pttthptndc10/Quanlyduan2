"""
Project Views — Quản lý Dự án với Django ORM.
"""

from django.shortcuts import render, redirect
from apps.projects.models import Project, ProjectMember
from apps.tasks.models import Task
from django.contrib.auth.models import User
from core.utils import get_user_from_session, is_admin_or_leader


def projects_list(request):
    user = get_user_from_session(request)
    projects = Project.objects.all().order_by('-updated_at')
    
    project_data = []
    for p in projects:
        tasks = p.tasks.all()
        done_count = tasks.filter(status='done').count()
        task_count = tasks.count()
        project_data.append({
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'deadline': p.deadline.isoformat() if p.deadline else None,
            'status': p.status,
            'priority': p.priority,
            'task_count': task_count,
            'done_count': done_count,
        })

    return render(request, 'projects/list.html', {'projects': project_data, 'user': user})


def project_detail(request, project_id):
    user = get_user_from_session(request)
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return redirect('/projects/')

    tasks = project.tasks.all().select_related('assignee').order_by('-created_at')
    members = project.members.all().select_related('user__profile')

    task_list = []
    for t in tasks:
        assignee_name = t.assignee.profile.full_name if (t.assignee and hasattr(t.assignee, 'profile')) else (t.assignee.email if t.assignee else '—')
        task_list.append({
            'id': t.id,
            'title': t.title,
            'status': t.status,
            'priority': t.priority,
            'progress': t.progress,
            'deadline': t.deadline.isoformat() if t.deadline else None,
            'assignee_id': assignee_name,
        })

    member_list = []
    for m in members:
        fn = m.user.profile.full_name if hasattr(m.user, 'profile') else m.user.email
        member_list.append({
            'member_id': m.user.id,
            'profiles': {'full_name': fn}
        })

    return render(request, 'projects/detail.html', {
        'project': {
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'deadline': project.deadline.isoformat() if project.deadline else None,
            'status': project.status,
            'priority': project.priority,
        },
        'tasks': task_list,
        'members': member_list,
        'user': user,
    })


def project_create(request):
    if not is_admin_or_leader(request):
        return redirect('/projects/')
    user = get_user_from_session(request)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        desc = request.POST.get('description', '').strip()
        dl = request.POST.get('deadline') or None
        st = request.POST.get('status', 'planning')
        pr = request.POST.get('priority', 'medium')

        if not name:
            return render(request, 'projects/form.html', {'error': 'Tên dự án không được trống', 'user': user, 'action': 'Tạo dự án'})

        creator = User.objects.get(id=user['id'])
        project = Project.objects.create(
            name=name, description=desc, deadline=dl,
            status=st, priority=pr, created_by=creator
        )
        ProjectMember.objects.create(project=project, user=creator, role='leader')

        return redirect('/projects/')

    return render(request, 'projects/form.html', {'user': user, 'action': 'Tạo dự án'})


def project_edit(request, project_id):
    if not is_admin_or_leader(request):
        return redirect(f'/projects/{project_id}/')
    user = get_user_from_session(request)

    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return redirect('/projects/')

    if request.method == 'POST':
        project.name = request.POST.get('name', '').strip()
        project.description = request.POST.get('description', '').strip()
        project.deadline = request.POST.get('deadline') or None
        project.status = request.POST.get('status', 'planning')
        project.priority = request.POST.get('priority', 'medium')
        project.save()
        return redirect(f'/projects/{project.id}/')

    return render(request, 'projects/form.html', {
        'project': {
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'deadline': project.deadline.isoformat() if project.deadline else None,
            'status': project.status,
            'priority': project.priority,
        },
        'user': user,
        'action': 'Chỉnh sửa dự án'
    })


def project_delete(request, project_id):
    if not is_admin_or_leader(request):
        return redirect('/projects/')
    if request.method == 'POST':
        Project.objects.filter(id=project_id).delete()
    return redirect('/projects/')
