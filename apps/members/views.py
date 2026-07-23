"""
Members Views — Danh sách và hồ sơ thành viên.
"""

from django.shortcuts import render, redirect
from apps.authentication.services.supabase_client import get_admin_supabase_client
from core.utils import get_user_from_session


def members_list(request):
    user = get_user_from_session(request)
    db = get_admin_supabase_client(request)
    try:
        members = db.table('profiles').select('*').order('full_name').execute().data or []
    except Exception:
        members = []
    return render(request, 'members/list.html', {'members': members, 'user': user})


def member_detail(request, member_id):
    user = get_user_from_session(request)
    db = get_admin_supabase_client(request)
    try:
        member = db.table('profiles').select('*').eq('id', member_id).single().execute().data
        tasks = db.table('tasks').select('id, title, status, priority, deadline, projects(name)') \
            .eq('assignee_id', member_id).order('created_at', desc=True).limit(10).execute().data or []
        project_ids = db.table('project_members').select('project_id').eq('member_id', member_id).execute().data or []
        pids = [p['project_id'] for p in project_ids]
        projects = db.table('projects').select('id, name, status').in_('id', pids).execute().data or [] if pids else []
    except Exception:
        return redirect('/members/')
    return render(request, 'members/detail.html', {
        'member': member, 'tasks': tasks, 'projects': projects, 'user': user,
    })
