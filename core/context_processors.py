"""
Core Context Processors — Cung cấp context dùng chung cho tất cả Django template.
"""

from apps.authentication.models import Profile

def global_context(request):
    user_id = request.session.get('user_id')
    user_email = request.session.get('user_email')
    user_name = request.session.get('user_name')
    user_role = request.session.get('user_role', 'member')

    current_user = None
    if user_id:
        try:
            profile = Profile.objects.select_related('user').get(user_id=user_id)
            user_name = profile.full_name
            user_role = profile.role
            request.session['user_name'] = user_name
            request.session['user_role'] = user_role
        except Exception:
            pass

        current_user = {
            'id': user_id,
            'email': user_email,
            'full_name': user_name or user_email,
            'role': user_role,
        }

    return {
        'current_user': current_user,
        'user_name': user_name,
        'user_role': user_role,
    }
