"""
Context processors — inject biến global vào tất cả template.
Tự động đồng bộ role người dùng từ Supabase profiles.
"""

from django.conf import settings
from core.utils import PROJECT_STATUS_LABELS, TASK_STATUS_LABELS, PRIORITY_LABELS, ROLE_LABELS


def global_context(request):
    """Cung cấp thông tin user và app cho mọi template."""
    user_id = request.session.get('user_id')
    user_role = request.session.get('user_role')
    user_name = request.session.get('user_name')

    # Tự động sync role mới nhất từ profiles table
    if user_id and user_role != 'admin':
        try:
            from apps.authentication.services.supabase_client import get_admin_supabase_client
            db = get_admin_supabase_client(request)
            res = db.table('profiles').select('role, full_name').eq('id', user_id).execute()
            if res.data:
                user_role = res.data[0].get('role', user_role)
                user_name = res.data[0].get('full_name', user_name)
                request.session['user_role'] = user_role
                request.session['user_name'] = user_name
        except Exception:
            pass

    return {
        'APP_NAME': settings.APP_NAME,
        'current_user': {
            'id':    user_id,
            'email': request.session.get('user_email'),
            'name':  user_name,
            'role':  user_role,
        } if user_id else None,
        'PROJECT_STATUS_LABELS': PROJECT_STATUS_LABELS,
        'TASK_STATUS_LABELS': TASK_STATUS_LABELS,
        'PRIORITY_LABELS': PRIORITY_LABELS,
        'ROLE_LABELS': ROLE_LABELS,
    }
