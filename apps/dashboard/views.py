"""
Dashboard Views — Trang tổng quan hệ thống.
Hiển thị thống kê: projects, tasks, members.
"""

from django.shortcuts import render
from apps.authentication.services.supabase_client import get_admin_supabase_client
from core.utils import get_user_from_session


def dashboard_view(request):
    user = get_user_from_session(request)
    db = get_admin_supabase_client(request)

    # Lấy thống kê tổng quan
    try:
        projects = db.table('projects').select('id, status').execute().data or []
        tasks    = db.table('tasks').select('id, status, deadline').execute().data or []
        members  = db.table('profiles').select('id, status').eq('status', 'active').execute().data or []

        from datetime import date
        today = date.today().isoformat()

        stats = {
            'total_projects':  len(projects),
            'active_projects': sum(1 for p in projects if p['status'] == 'in_progress'),
            'total_tasks':     len(tasks),
            'done_tasks':      sum(1 for t in tasks if t['status'] == 'done'),
            'overdue_tasks':   sum(1 for t in tasks if t.get('deadline') and t['deadline'] < today and t['status'] not in ('done', 'cancelled')),
            'blocked_tasks':   sum(1 for t in tasks if t['status'] == 'blocked'),
            'total_members':   len(members),
        }

        # 5 task gần nhất được giao cho mình
        my_tasks = db.table('tasks').select('id, title, status, priority, deadline, project_id') \
            .eq('assignee_id', user['id']) \
            .neq('status', 'done').neq('status', 'cancelled') \
            .order('created_at', desc=True).limit(5).execute().data or []

        # 5 project gần nhất
        recent_projects = db.table('projects').select('id, name, status, priority, deadline') \
            .order('updated_at', desc=True).limit(5).execute().data or []

    except Exception as e:
        stats = {'total_projects': 0, 'active_projects': 0, 'total_tasks': 0,
                 'done_tasks': 0, 'overdue_tasks': 0, 'blocked_tasks': 0, 'total_members': 0}
        my_tasks = []
        recent_projects = []

    return render(request, 'dashboard/dashboard.html', {
        'stats': stats,
        'my_tasks': my_tasks,
        'recent_projects': recent_projects,
        'user': user,
    })
