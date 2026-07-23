"""
Task Views — Quản lý công việc (Kanban + danh sách).
"""

import json
from datetime import date
from django.shortcuts import render, redirect
from django.http import JsonResponse
from apps.authentication.services.supabase_client import get_admin_supabase_client
from core.utils import get_user_from_session, TASK_STATUS_LABELS


def tasks_list(request):
    user = get_user_from_session(request)
    db = get_admin_supabase_client(request)
    try:
        tasks = db.table('tasks').select('*, projects(name)').order('created_at', desc=True).execute().data or []
        profiles = db.table('profiles').select('id, full_name').execute().data or []
        prof_map = {p['id']: p['full_name'] for p in profiles}
        for t in tasks:
            t['assignee_name'] = prof_map.get(t.get('assignee_id'), 'Chưa giao')
    except Exception:
        tasks = []
    return render(request, 'tasks/list.html', {
        'tasks': tasks, 'user': user,
        'today': date.today().isoformat(),
        'status_labels': TASK_STATUS_LABELS,
    })


def task_detail(request, task_id):
    user = get_user_from_session(request)
    db = get_admin_supabase_client(request)
    try:
        task = db.table('tasks').select('*, projects(name, id), profiles!tasks_assignee_id_fkey(full_name)') \
            .eq('id', task_id).single().execute().data
    except Exception:
        return redirect('/tasks/')
    return render(request, 'tasks/detail.html', {'task': task, 'user': user})


def task_create(request):
    user = get_user_from_session(request)
    db = get_admin_supabase_client(request)
    projects = db.table('projects').select('id, name').execute().data or []
    members  = db.table('profiles').select('id, full_name').eq('status', 'active').execute().data or []
    if request.method == 'POST':
        data = {
            'title': request.POST.get('title', '').strip(),
            'description': request.POST.get('description', '').strip(),
            'project_id': request.POST.get('project_id') or None,
            'assignee_id': request.POST.get('assignee_id') or None,
            'deadline': request.POST.get('deadline') or None,
            'status': request.POST.get('status', 'todo'),
            'priority': request.POST.get('priority', 'medium'),
            'created_by': user['id'],
        }
        if not data['title']:
            return render(request, 'tasks/form.html', {'error': 'Tiêu đề không được trống', 'projects': projects, 'members': members, 'user': user, 'action': 'Tạo công việc'})
        db.table('tasks').insert(data).execute()
        return redirect('/tasks/')
    return render(request, 'tasks/form.html', {'projects': projects, 'members': members, 'user': user, 'action': 'Tạo công việc'})


def task_edit(request, task_id):
    user = get_user_from_session(request)
    db = get_admin_supabase_client(request)
    task = db.table('tasks').select('*').eq('id', task_id).single().execute().data
    projects = db.table('projects').select('id, name').execute().data or []
    members  = db.table('profiles').select('id, full_name').eq('status', 'active').execute().data or []
    if request.method == 'POST':
        data = {
            'title': request.POST.get('title', '').strip(),
            'description': request.POST.get('description', '').strip(),
            'project_id': request.POST.get('project_id') or None,
            'assignee_id': request.POST.get('assignee_id') or None,
            'deadline': request.POST.get('deadline') or None,
            'status': request.POST.get('status', 'todo'),
            'priority': request.POST.get('priority', 'medium'),
            'progress': int(request.POST.get('progress', 0)),
        }
        db.table('tasks').update(data).eq('id', task_id).execute()
        return redirect(f'/tasks/{task_id}/')
    return render(request, 'tasks/form.html', {'task': task, 'projects': projects, 'members': members, 'user': user, 'action': 'Chỉnh sửa công việc'})


def task_delete(request, task_id):
    if request.method == 'POST':
        get_admin_supabase_client(request).table('tasks').delete().eq('id', task_id).execute()
    return redirect('/tasks/')


def update_task_status(request):
    """AJAX: Cập nhật status task từ Kanban board."""
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)
    try:
        data = json.loads(request.body)
        task_id = data['task_id']
        new_status = data['status']
        get_admin_supabase_client(request).table('tasks').update({'status': new_status}).eq('id', task_id).execute()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
