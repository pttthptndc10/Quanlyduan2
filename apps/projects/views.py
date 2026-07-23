"""
Project Views — Quản lý dự án.
"""

import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from apps.authentication.services.supabase_client import get_admin_supabase_client
from core.utils import get_user_from_session, is_admin_or_leader


def projects_list(request):
    user = get_user_from_session(request)
    db = get_admin_supabase_client(request)
    try:
        projects = db.table('projects').select('*').order('updated_at', desc=True).execute().data or []
        # Lấy số lượng task cho mỗi project
        for p in projects:
            tasks_res = db.table('tasks').select('id, status').eq('project_id', p['id']).execute().data or []
            p['task_count'] = len(tasks_res)
            p['done_count'] = sum(1 for t in tasks_res if t['status'] == 'done')
    except Exception:
        projects = []
    return render(request, 'projects/list.html', {'projects': projects, 'user': user})


def project_detail(request, project_id):
    user = get_user_from_session(request)
    db = get_admin_supabase_client(request)
    try:
        project = db.table('projects').select('*').eq('id', project_id).single().execute().data
        tasks = db.table('tasks').select('*').eq('project_id', project_id).order('created_at').execute().data or []
        members_res = db.table('project_members').select('*, profiles(*)').eq('project_id', project_id).execute().data or []
        
        # Map profiles for assignee names
        profiles = db.table('profiles').select('id, full_name').execute().data or []
        prof_map = {p['id']: p['full_name'] for p in profiles}
        for t in tasks:
            t['assignee_name'] = prof_map.get(t.get('assignee_id'), 'Chưa giao')
    except Exception:
        return redirect('/projects/')
    return render(request, 'projects/detail.html', {
        'project': project, 'tasks': tasks,
        'members': members_res, 'user': user,
    })


def project_create(request):
    if not is_admin_or_leader(request):
        return redirect('/projects/')
    user = get_user_from_session(request)
    if request.method == 'POST':
        db = get_admin_supabase_client(request)
        data = {
            'name': request.POST.get('name', '').strip(),
            'description': request.POST.get('description', '').strip(),
            'deadline': request.POST.get('deadline') or None,
            'status': request.POST.get('status', 'planning'),
            'priority': request.POST.get('priority', 'medium'),
            'created_by': user['id'],
        }
        if not data['name']:
            return render(request, 'projects/form.html', {'error': 'Tên dự án không được trống', 'user': user, 'action': 'Tạo dự án'})
        db.table('projects').insert(data).execute()
        return redirect('/projects/')
    return render(request, 'projects/form.html', {'user': user, 'action': 'Tạo dự án'})


def project_edit(request, project_id):
    if not is_admin_or_leader(request):
        return redirect(f'/projects/{project_id}/')
    user = get_user_from_session(request)
    db = get_admin_supabase_client(request)
    project = db.table('projects').select('*').eq('id', project_id).single().execute().data
    if request.method == 'POST':
        data = {
            'name': request.POST.get('name', '').strip(),
            'description': request.POST.get('description', '').strip(),
            'deadline': request.POST.get('deadline') or None,
            'status': request.POST.get('status', 'planning'),
            'priority': request.POST.get('priority', 'medium'),
        }
        db.table('projects').update(data).eq('id', project_id).execute()
        return redirect(f'/projects/{project_id}/')
    return render(request, 'projects/form.html', {'project': project, 'user': user, 'action': 'Chỉnh sửa dự án'})


def project_delete(request, project_id):
    if not is_admin_or_leader(request):
        return redirect('/projects/')
    if request.method == 'POST':
        db = get_admin_supabase_client(request)
        db.table('projects').delete().eq('id', project_id).execute()
    return redirect('/projects/')
