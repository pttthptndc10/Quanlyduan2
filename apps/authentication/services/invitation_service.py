"""
Invitation Service — Quản lý lời mời đăng ký bằng Django ORM.
"""

import uuid
from datetime import datetime, timezone, timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from apps.authentication.models import Invitation


def create_invitation(email: str, full_name: str, invited_by_id: int) -> dict:
    """Tạo mới hoặc cập nhật lời mời (update_or_create) và gửi email."""
    try:
        now = datetime.now(timezone.utc)
        token = str(uuid.uuid4())
        expires_at = now + timedelta(hours=24)
        invited_by = User.objects.filter(id=invited_by_id).first() if invited_by_id else None

        invitation, _ = Invitation.objects.update_or_create(
            email=email,
            defaults={
                'full_name': full_name,
                'token': token,
                'invited_by': invited_by,
                'used': False,
                'expires_at': expires_at,
            }
        )

        url = f"{settings.APP_BASE_URL}/register/?token={token}"
        _send_invite_email(email, full_name, url)

        return {'success': True, 'token': token, 'invitation_url': url}

    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_valid_invitation(token: str) -> dict | None:
    """Lấy lời mời hợp lệ."""
    try:
        now = datetime.now(timezone.utc)
        inv = Invitation.objects.filter(token=token, used=False, expires_at__gt=now).first()
        if not inv:
            return None
        return {
            'id': inv.id,
            'email': inv.email,
            'full_name': inv.full_name,
            'role': inv.role,
            'token': inv.token,
            'expires_at': inv.expires_at.isoformat(),
        }
    except Exception:
        return None


def get_all_invitations() -> list:
    """Lấy tất cả danh sách lời mời."""
    try:
        invs = Invitation.objects.all().order_by('-created_at')[:50]
        return [
            {
                'id': i.id,
                'email': i.email,
                'full_name': i.full_name or i.email.split('@')[0],
                'role': i.role,
                'used': i.used,
                'expires_at': i.expires_at.strftime('%Y-%m-%d %H:%M'),
            }
            for i in invs
        ]
    except Exception:
        return []


def revoke_invitation(inv_id: int) -> dict:
    """Thu hồi lời mời."""
    try:
        inv = Invitation.objects.filter(id=inv_id, used=False).first()
        if inv:
            inv.used = True
            inv.save()
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def _send_invite_email(email: str, full_name: str, url: str) -> None:
    subject = "[WebNoiBO] Lời mời tham gia hệ thống quản lý"
    message = f"Xin chào {full_name},\n\nBạn được mời tham gia WebNoiBO.\nNhấn vào liên kết sau để đăng ký:\n{url}\n\nTrân trọng,\nWebNoiBO Team"
    try:
        send_mail(subject, message, getattr(settings, 'DEFAULT_FROM_EMAIL', 'webnoibo@gmail.com'), [email], fail_silently=True)
    except Exception:
        pass
