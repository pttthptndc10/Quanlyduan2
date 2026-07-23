"""
Invitation Service — Quản lý lời mời đăng ký hệ thống.
Chỉ admin/leader mới được tạo lời mời.
"""

import uuid
from datetime import datetime, timezone, timedelta
from django.core.mail import send_mail
from django.conf import settings

from .supabase_client import get_admin_supabase_client


def create_invitation(email: str, full_name: str, invited_by_id: str) -> dict:
    """Tạo lời mời mới và gửi email."""
    try:
        db = get_admin_supabase_client()
        now = datetime.now(timezone.utc)

        # Kiểm tra đã có lời mời chờ chưa
        existing = db.table('invitations').select('id') \
            .eq('email', email).eq('used', False) \
            .gt('expires_at', now.isoformat()).execute()

        if existing.data:
            return {'success': False, 'error': f'{email} đã có lời mời đang chờ. Thu hồi trước.'}

        token = str(uuid.uuid4())
        expires_at = now + timedelta(hours=24)

        db.table('invitations').insert({
            'email': email,
            'full_name': full_name,
            'token': token,
            'invited_by': invited_by_id,
            'used': False,
            'expires_at': expires_at.isoformat(),
        }).execute()

        url = f"{settings.APP_BASE_URL}/register/?token={token}"
        _send_invite_email(email, full_name, url)

        return {'success': True, 'token': token, 'invitation_url': url}

    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_valid_invitation(token: str) -> dict | None:
    """Lấy lời mời hợp lệ (chưa dùng, chưa hết hạn)."""
    try:
        db = get_admin_supabase_client()
        res = db.table('invitations').select('*').eq('token', token).eq('used', False).execute()

        if not res.data:
            return None

        inv = res.data[0]
        exp = datetime.fromisoformat(inv['expires_at'].replace('Z', '+00:00'))
        if datetime.now(timezone.utc) > exp:
            return None

        return inv
    except Exception:
        return None


def mark_invitation_used(token: str) -> None:
    """Đánh dấu lời mời đã sử dụng."""
    try:
        db = get_admin_supabase_client()
        db.table('invitations').update({
            'used': True,
            'used_at': datetime.now(timezone.utc).isoformat()
        }).eq('token', token).execute()
    except Exception:
        pass


def get_all_invitations() -> list:
    """Lấy danh sách lời mời gần đây (50 cái mới nhất)."""
    try:
        db = get_admin_supabase_client()
        res = db.table('invitations').select('*').order('created_at', desc=True).limit(50).execute()
        return res.data or []
    except Exception:
        return []


def revoke_invitation(inv_id: str) -> dict:
    """Thu hồi lời mời chưa dùng."""
    try:
        db = get_admin_supabase_client()
        db.table('invitations').update({
            'used': True,
            'used_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', inv_id).eq('used', False).execute()
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def _send_invite_email(email: str, full_name: str, url: str) -> None:
    """Gửi email chứa link mời."""
    app = settings.APP_NAME
    send_mail(
        subject=f'[{app}] Bạn được mời tham gia hệ thống',
        message=(
            f"Xin chào {full_name},\n\n"
            f"Bạn được mời tham gia {app}.\n\n"
            f"Link đăng ký (dùng 1 lần, hết hạn 24h):\n{url}\n\n"
            f"Trân trọng,\nTeam {app}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
