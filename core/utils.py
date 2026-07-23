"""
Core utilities — các hàm dùng chung toàn project.
"""

from django.conf import settings


# ─── Session helpers ──────────────────────────────────────────────────────────

def get_user_from_session(request) -> dict | None:
    """Lấy thông tin user hiện tại từ session. Trả về None nếu chưa đăng nhập."""
    if not request.session.get('user_id'):
        return None
    return {
        'id': request.session.get('user_id'),
        'email': request.session.get('user_email'),
        'name': request.session.get('user_name'),
        'role': request.session.get('user_role'),
    }


def is_admin(request) -> bool:
    return request.session.get('user_role') == 'admin'


def is_admin_or_leader(request) -> bool:
    return request.session.get('user_role') in ('admin', 'leader')


# ─── Label mappings (tiếng Việt) ─────────────────────────────────────────────

PROJECT_STATUS_LABELS = {
    'planning':    'Lên kế hoạch',
    'in_progress': 'Đang thực hiện',
    'review':      'Đang review',
    'completed':   'Hoàn thành',
    'paused':      'Tạm dừng',
}

TASK_STATUS_LABELS = {
    'todo':      'Việc cần làm',
    'doing':     'Đang làm',
    'review':    'Đang review',
    'done':      'Xong',
    'blocked':   'Bị chặn',
    'cancelled': 'Đã hủy',
}

PRIORITY_LABELS = {
    'low':      'Thấp',
    'medium':   'Trung bình',
    'high':     'Cao',
    'critical': 'Khẩn cấp',
}

ROLE_LABELS = {
    'admin':  'Quản trị viên',
    'leader': 'Trưởng nhóm',
    'member': 'Thành viên',
}

# Màu badge cho status
STATUS_COLORS = {
    'planning':    '#64748b',
    'in_progress': '#06b6d4',
    'review':      '#f59e0b',
    'completed':   '#22c55e',
    'paused':      '#94a3b8',
    'todo':        '#64748b',
    'doing':       '#06b6d4',
    'done':        '#22c55e',
    'blocked':     '#ef4444',
    'cancelled':   '#6b7280',
}

PRIORITY_COLORS = {
    'low':      '#64748b',
    'medium':   '#06b6d4',
    'high':     '#f59e0b',
    'critical': '#ef4444',
}
